"""Validate the fixed 20-query workload against a hand-reviewed semantic oracle.

Run AFTER python -m benchmark; this tool consumes its unchanged raw output.
All database commands are SELECT or transaction-local controls; no index DDL.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re

import psycopg
from dotenv import load_dotenv

from advisor.candidates import make_candidates
from advisor.cost_model import estimated_index_bytes, score_candidate
from advisor.parser import parse_workload
from advisor.statistics import read_statistics
from benchmark.runner import timestamp
from benchmark.sql import split_workload
from workload.benchmark20_manifest import CASES

ROOT = Path(__file__).resolve().parent.parent


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def audit_advisor(source, tables):
    statements = split_workload(source)
    if len(statements) != len(CASES):
        raise ValueError("The frozen coverage matrix requires exactly 20 queries")
    columns = {name: set(table.columns) for name, table in tables.items()}
    results = []
    for statement, expected in zip(statements, CASES):
        parsed = parse_workload(statement.sql, columns=columns)
        predicates = [tuple(asdict(p).values()) for q in parsed.queries for p in q.predicates]
        candidates = make_candidates(parsed.queries, tables, max_columns=3, max_candidates=None)
        actual_candidates = sorted((c.table, c.columns) for c in candidates)
        expected_candidates = sorted(expected["candidates"])
        if expected["unsupported"]:
            correct = (not parsed.queries and len(parsed.warnings) == 1
                       and expected["unsupported"] in parsed.warnings[0] and not candidates)
            classification = "unsupported_syntax"
        else:
            correct = (len(parsed.queries) == 1 and not parsed.warnings
                       and Counter(predicates) == Counter(expected["predicates"])
                       and actual_candidates == expected_candidates)
            classification = "parsed_with_candidates" if candidates else "parsed_without_composite_candidates"
        results.append({
            "number": expected["number"], "sql_sha256": sha(statement.sql),
            "semantic_check_passed": correct, "classification": classification,
            "expected_predicates": expected["predicates"], "actual_predicates": predicates,
            "expected_candidates": expected_candidates, "actual_candidates": actual_candidates,
            "expected_join_pairs": expected["joins"], "warnings": list(parsed.warnings),
        })
    whole = parse_workload(source, columns=columns)
    return results, whole, make_candidates(whole.queries, tables, max_candidates=None)


def read_only_rows(connection, sql):
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = 60000")
        cursor.execute("SET LOCAL standard_conforming_strings = on")
        cursor.execute(sql, binary=True, prepare=False)
        return cursor.fetchall()


def snapshot(connection):
    rows = read_only_rows(connection, "SELECT (SELECT count(*) FROM tpch.orders), "
                          "(SELECT count(*) FROM tpch.lineitem)")[0]
    return {
        "row_counts": dict(zip(("orders", "lineitem"), rows)),
        "indexes": read_only_rows(connection, "SELECT tablename,indexname,indexdef FROM pg_indexes "
                                  "WHERE schemaname='tpch' ORDER BY tablename,indexname"),
        "columns": read_only_rows(connection, "SELECT table_name,column_name,data_type,is_nullable "
                                  "FROM information_schema.columns WHERE table_schema='tpch' "
                                  "ORDER BY table_name,ordinal_position"),
        "relations": read_only_rows(connection, "SELECT c.relname,pg_relation_size(c.oid),pg_total_relation_size(c.oid) "
                                    "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                                    "WHERE n.nspname='tpch' AND c.relkind='r' ORDER BY c.relname"),
    }


def walk_plan(node):
    yield node
    for child in node.get("Plans", []):
        yield from walk_plan(child)


def validate(connection, source, baseline):
    statements = split_workload(source)
    if baseline["status"] != "ok" or baseline["workload_sha256"] != sha(source):
        raise ValueError("Benchmark must be successful and match the exact workload hash")
    if len(baseline["queries"]) != len(CASES):
        raise ValueError("Benchmark must contain all 20 queries")
    connection.read_only = True
    before = snapshot(connection)
    with connection.transaction(force_rollback=True):
        tables = read_statistics(connection)
    results, parsed, candidates = audit_advisor(source, tables)
    join_base = read_only_rows(connection, "SELECT count(*) FROM tpch.orders JOIN tpch.lineitem "
                               "ON orders.o_orderkey=lineitem.l_orderkey")[0][0]
    output_digests = {}
    for result, statement, expected, measured in zip(results, statements, CASES, baseline["queries"]):
        if (measured["number"] != result["number"] or measured["status"] != "ok"
                or measured["sql_sha256"] != sha(statement.sql)):
            raise ValueError("Benchmark query identity or completion mismatch")
        rows = read_only_rows(connection, statement.sql)
        output_digests[result["number"]] = sha(json.dumps(rows, default=str, ensure_ascii=False))
        result["returned_rows"] = len(rows)
        result["result_sha256"] = output_digests[result["number"]]
        probes = {}
        for table, condition in expected["filters"].items():
            count = read_only_rows(connection, f"SELECT count(*) FROM tpch.{table} WHERE {condition}")[0][0]
            probes[table] = {"where": condition, "matching_rows": count,
                             "base_rows": before["row_counts"][table],
                             "fraction": count / before["row_counts"][table]}
        result["local_filter_selectivity"] = probes
        if expected["joins"]:
            conditions = " AND ".join(f"({text})" for text in expected["filters"].values())
            count = read_only_rows(connection, "SELECT count(*) FROM tpch.orders JOIN tpch.lineitem "
                                   "ON orders.o_orderkey=lineitem.l_orderkey WHERE " + conditions)[0][0]
            result["joined_matching_rows"] = count
            result["unfiltered_join_rows"] = join_base
        nodes = list(walk_plan(measured["measurements"][0]["query_plan"][0]["Plan"]))
        aliases = {node.get("Alias", node["Relation Name"]): node["Relation Name"]
                   for node in nodes if "Relation Name" in node}
        result["plan_relation_aliases"] = aliases
        result["plan_alias_check_passed"] = aliases == expected["aliases"]
        result["plan_evidence"] = [{key: node[key] for key in (
            "Node Type", "Relation Name", "Alias", "Actual Rows", "Actual Loops",
            "Filter", "Hash Cond", "Merge Cond", "Join Filter", "Index Cond") if key in node} for node in nodes]
        join_conditions = [node[key] for node in nodes for key in ("Hash Cond", "Merge Cond", "Join Filter") if key in node]
        expected_join_fields = {f"{alias}.{column}" for left, lc, right, rc in expected["joins"]
                                for table, column in ((left, lc), (right, rc))
                                for alias, base in expected["aliases"].items() if table == base}
        actual_join_fields = set(re.findall(r"\b[ol]\.[a-z_]+\b", " ".join(join_conditions)))
        result["postgres_join_check_passed"] = actual_join_fields == expected_join_fields
        result["advisor_join_endpoint_check"] = ("whole_query_skipped" if expected["unsupported"]
            else "passed" if {p[:3] for p in result["actual_predicates"] if p[3] == "join"}
                 == {(schema, table, column) for schema, table, column, kind, _ in expected["predicates"] if kind == "join"}
            else "failed")
        result["benchmark_summary"] = measured["summary"]
    after = snapshot(connection)
    candidate_details = [{"label": c.label, "estimated_bytes": estimated_index_bytes(c, tables[c.table]),
                          "generated_by_queries": [r["number"] for r in results
                            if (c.table, c.columns) in r["actual_candidates"]]} for c in candidates]
    consistent = before == after
    equivalent = output_digests[1] == output_digests[20]
    shared = next(c for c in candidates if c.table == "orders" and c.columns == ("o_orderstatus", "o_orderdate"))
    q1_score = score_candidate(shared, (parsed.queries[0],), tables).independent_benefit
    q2_score = score_candidate(shared, (parsed.queries[1],), tables).independent_benefit
    source_bindings = []
    for statement in statements:
        source_bindings.append(re.findall(r"\b(?:FROM|JOIN)\s+tpch\.(orders|lineitem)", statement.sql, re.I))
    passed = all(r["semantic_check_passed"] and r["plan_alias_check_passed"]
                 and r["postgres_join_check_passed"] for r in results)
    return {
        "created_at": timestamp(), "workload_sha256": sha(source),
        "semantic_audit_passed": passed, "database_unchanged": consistent,
        "q01_q20_results_equal": equivalent, "before": before, "after": after,
        "catalog": {name: asdict(table) for name, table in tables.items()},
        "parsed_query_numbers": [q.number for q in parsed.queries],
        "skipped_query_numbers": [e["number"] for e in CASES if e["unsupported"]],
        "whole_workload_warnings": list(parsed.warnings), "queries": results,
        "candidate_count": len(candidates), "candidates": candidate_details,
        "estimated_all_candidate_bytes": sum(c["estimated_bytes"] for c in candidate_details),
        "q01_q02_same_index_heuristic_scores": [q1_score, q2_score],
        "environment": read_only_rows(connection, "SELECT version(),current_setting('shared_buffers'),"
                                      "current_setting('effective_cache_size'),current_setting('work_mem')")[0],
        "source_relation_bindings": source_bindings,
        "note": "Unsupported syntax is an expected coverage outcome, not successful Advisor parsing. "
                "Candidate sizes are heuristic; no indexes were created.",
        "passed": passed and consistent and equivalent,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, default=ROOT / "workload/benchmark20.sql")
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output already exists; choose a new path")
    source = args.workload.read_bytes().decode("utf-8-sig")
    baseline = json.loads(args.benchmark.read_text(encoding="utf-8"))
    load_dotenv(ROOT / ".env")
    with psycopg.connect(autocommit=True, connect_timeout=5, prepare_threshold=None) as connection:
        report = validate(connection, source, baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("passed", "semantic_audit_passed", "database_unchanged",
                     "parsed_query_numbers", "skipped_query_numbers", "candidate_count", "estimated_all_candidate_bytes")}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
