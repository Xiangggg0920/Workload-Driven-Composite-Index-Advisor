"""3B: read-only capacity simulation using the unchanged Advisor implementation.

Requires successful 3A acceptance. No SQL from the workload is executed, no
EXPLAIN ANALYZE is run, and no indexes or PostgreSQL objects are created.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from advisor.cost_model import score_candidates
from advisor.main import _budget_shortlist
from advisor.optimizer import _gain, select_indexes
from advisor.statistics import read_statistics
from dataset.prepare_sf1 import ROOT, TARGET
from dataset.verify_sf1 import accept_checks
from workload.validate_benchmark20 import audit_advisor

MIB = 1024**2
FORMAL_BUDGETS_MIB = (100, 500, 1024)


def require_acceptance(acceptance):
    if (acceptance.get("database") != TARGET or not acceptance.get("passed")
            or not accept_checks(acceptance.get("checks", {}))):
        raise ValueError("3A acceptance did not pass; 3B must not start")


def selection_record(scored, budget_bytes, identifiers):
    shortlisted, truncated = _budget_shortlist(scored, budget_bytes, 40)
    selection = select_indexes(shortlisted, budget_bytes)
    dimension_count = len(scored[0].savings_by_query) if scored else 0
    coverage = tuple(max((s.savings_by_query[i] for s in selection.selected), default=0.0)
                     for i in range(dimension_count))
    remaining = budget_bytes - selection.used_bytes
    chosen = {item.index for item in selection.selected}
    omitted_positive_gain = [{"id": identifiers[item.index.label], "estimated_bytes": item.estimated_bytes,
                             "marginal_score": _gain(item, coverage),
                             "fits_remaining_budget": item.estimated_bytes <= remaining}
                            for item in scored if item.index not in chosen and _gain(item, coverage) > 1e-9]
    return {
        "budget_bytes": budget_bytes, "budget_mib": budget_bytes / MIB,
        "eligible_candidate_count": sum(s.estimated_bytes <= budget_bytes and s.independent_benefit > 0 for s in scored),
        "optimizer_candidate_count": len(shortlisted), "candidate_limit_applied": truncated,
        "selection_method": ("exact-within-shortlist" if selection.exact and truncated else
                             "exact" if selection.exact else "marginal-greedy"),
        "selected_ids": [identifiers[item.index.label] for item in selection.selected],
        "selected_labels": [item.index.label for item in selection.selected],
        "selected_count": len(selection.selected), "estimated_selected_bytes": selection.used_bytes,
        "estimated_selected_mib": selection.used_bytes / MIB,
        "unused_bytes": remaining, "utilization": selection.used_bytes / budget_bytes if budget_bytes else 0,
        "estimated_workload_score": selection.estimated_benefit,
        "omitted_positive_marginal_candidates": omitted_positive_gain,
        "budget_blocks_further_positive_additions": bool(omitted_positive_gain)
            and not any(item["fits_remaining_budget"] for item in omitted_positive_gain),
        "actual_index_bytes": None,
    }


def simulate(queries, tables, candidates, query_audit):
    scored = score_candidates(candidates, queries, tables)
    scored.sort(key=lambda item: item.index.label)
    identifiers = {item.index.label: f"C{i:02d}" for i, item in enumerate(scored, 1)}
    details = [{"id": identifiers[s.index.label], "label": s.index.label,
                "schema": s.index.schema, "table": s.index.table, "columns": list(s.index.columns),
                "estimated_bytes": s.estimated_bytes, "estimated_mib": s.estimated_bytes / MIB,
                "independent_score": s.independent_benefit, "score_vector": list(s.savings_by_query),
                "generated_by_queries": [q["number"] for q in query_audit
                    if (s.index.table, s.index.columns) in q["actual_candidates"]],
                "actual_index_bytes": None} for s in scored]
    total = sum(s.estimated_bytes for s in scored)
    ceiling = sum(max((s.savings_by_query[i] for s in scored), default=0)
                  for i in range(len(scored[0].savings_by_query) if scored else 0))
    budgets = [selection_record(scored, mib * MIB, identifiers) for mib in FORMAL_BUDGETS_MIB]
    reference = selection_record(scored, max(total, 1), identifiers)
    for budget in budgets:
        budget["score_fraction_of_model_ceiling"] = budget["estimated_workload_score"] / ceiling if ceiling else 0
        budget["score_gap_to_model_ceiling"] = ceiling - budget["estimated_workload_score"]
    dimensions = [{"query": q.number, "table": table} for q in queries for table in sorted(tables)]
    return {"candidate_count": len(scored), "candidates": details,
            "estimated_all_candidate_bytes": total, "estimated_all_candidate_mib": total / MIB,
            "score_dimensions": dimensions, "budgets": budgets,
            "model_score_ceiling": ceiling, "unconstrained_heuristic_reference": reference,
            "distinct_formal_selections": len({tuple(sorted(b["selected_ids"])) for b in budgets}),
            "distinct_formal_scores": len({round(b["estimated_workload_score"], 7) for b in budgets})}


def analyze(connection, source, acceptance):
    require_acceptance(acceptance)
    connection.read_only = True
    connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SELECT current_database(),current_setting('transaction_read_only'),"
                       "current_setting('server_version')")
        database, read_only, version = cursor.fetchone()
        if database != TARGET or read_only != "on":
            raise ValueError("3B must connect read-only to advisor_benchmark")
        tables = read_statistics(connection)
        cursor.execute("SELECT relname,last_analyze,last_autoanalyze,last_autovacuum "
                       "FROM pg_stat_all_tables WHERE schemaname='tpch' ORDER BY relname")
        maintenance = [{"table": name, "last_analyze": str(analyzed), "last_autoanalyze": str(auto),
                        "last_autovacuum": str(vacuum)} for name, analyzed, auto, vacuum in cursor.fetchall()]
        cursor.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='tpch'")
        before_indexes = cursor.fetchall()
        if before_indexes:
            raise ValueError("Expected an index-free 3A baseline; do not change or remove existing indexes")
        audit, parsed, candidates = audit_advisor(source, tables)
        if not all(q["semantic_check_passed"] for q in audit):
            raise ValueError("Workload semantic audit failed; no Parser rewrite is authorized")
        result = simulate(parsed.queries, tables, candidates, audit)
        cursor.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='tpch'")
        after_indexes = cursor.fetchall()
    return {
        "created_at": datetime.now(timezone.utc).isoformat(), "database": database,
        "server_version": version, "transaction_read_only": read_only,
        "scope": "3B estimates and simulations only; 3C not started",
        "workload_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "settings": {"max_columns": 3, "max_candidates": 40, "weights": "all 1", "exact_limit": 16,
                     "formal_budgets_mib": list(FORMAL_BUDGETS_MIB)},
        "parsed_queries": [q.number for q in parsed.queries],
        "skipped_queries": [q["number"] for q in audit if q["classification"] == "unsupported_syntax"],
        "parsed_without_composite_candidates": [q["number"] for q in audit if q["classification"] == "parsed_without_composite_candidates"],
        "warnings": list(parsed.warnings), "query_audit": audit,
        "catalog": {name: asdict(table) for name, table in tables.items()},
        "catalog_sha256": hashlib.sha256(json.dumps({name: asdict(table) for name, table in tables.items()},
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "maintenance_at_capture": maintenance,
        "indexes_before": before_indexes, "indexes_after": after_indexes,
        **result,
        "disclaimer": "Index bytes and scores are heuristic estimates, not measured index pg_relation_size, "
                      "latency or buffer savings. Heap bytes in catalog are actual table measurements. "
                      "The unconstrained greedy reference reaches the model ceiling but is not a minimum-size "
                      "or globally optimal configuration. Skipped queries are excluded from Advisor scoring.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--workload", type=Path, default=ROOT / "workload/benchmark20.sql")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output exists; never overwrite simulation evidence")
    acceptance = json.loads(args.acceptance.read_text(encoding="utf-8"))
    require_acceptance(acceptance)
    source = args.workload.read_bytes().decode("utf-8-sig")
    load_dotenv(ROOT / ".env")
    with psycopg.connect(dbname=TARGET, autocommit=True, connect_timeout=5, prepare_threshold=None) as connection:
        report = analyze(connection, source, acceptance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"candidate_count": report["candidate_count"],
                      "all_candidate_mib": report["estimated_all_candidate_mib"],
                      "budgets": [{k: b[k] for k in ("budget_mib", "selected_count", "estimated_selected_mib",
                         "estimated_workload_score", "selection_method", "score_fraction_of_model_ceiling")}
                                  for b in report["budgets"]],
                      "reference": report["unconstrained_heuristic_reference"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
