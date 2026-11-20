"""Freeze fair, auditable configurations before any index is built."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import re

from advisor.candidates import IndexCandidate
from advisor.cost_model import estimated_index_bytes
from advisor.statistics import ColumnStats, TableStats
from analysis.sf1_budget import simulate, require_acceptance
from benchmark.runner import BenchmarkConfig
from benchmark.sql import split_workload, validate_query
from dataset.prepare_sf1 import ROOT, TARGET
from workload.benchmark20_manifest import CASES
from workload.validate_benchmark20 import audit_advisor

STRATEGIES = ("baseline", "single", "suboptimal", "advisor")
BUDGETS = (100, 500, 1024)
MIB = 1024**2
WILLIAMS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8")).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset_hashes():
    paths = [ROOT / "workload/benchmark20.sql", ROOT / "workload/benchmark20_manifest.py"]
    for directory in ("advisor", "benchmark", "strategy_benchmark"):
        paths.extend(sorted((ROOT / directory).glob("*.py")))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def tables_from_report(report):
    return {name: TableStats(t["schema"], t["table"], t["rows"], t["heap_bytes"],
            {col: ColumnStats(**stat) for col, stat in t["columns"].items()})
            for name, t in report["catalog"].items()}


def controls(tables):
    """Use the full hand-reviewed workload, including the four unsupported cases.

    Single: every referenced predicate/join column. Composite: first-occurrence
    WHERE-then-ON column order, max three, one maximal index per query/table.
    Rank both by referenced-query count, estimated bytes, label. Never use
    measured latency or Advisor benefit scores to tune a control configuration.
    """
    fields = {}
    single, composite = {}, {}
    canonical = {}
    source_orders = defaultdict(list)
    generated = defaultdict(set)
    for case in CASES:
        per_table = defaultdict(list)
        for schema, table, col, _, _ in case["predicates"]:
            if col not in per_table[table]:
                per_table[table].append(col)
            if col not in tables[table].columns:
                raise ValueError("Manual workload manifest does not match the catalog")
        fields[case["number"]] = per_table
        for table, cols in per_table.items():
            for col in cols:
                index = IndexCandidate("tpch", table, (col,))
                single[index.label] = index
                generated[index.label].add(case["number"])
            if len(cols) >= 2:
                index = IndexCandidate("tpch", table, tuple(cols[:3]))
                key = (table, frozenset(index.columns))
                label = canonical.setdefault(key, index.label)
                if label == index.label:
                    composite[label] = index
                generated[label].add(case["number"])
                source_orders[label].append({"query": case["number"], "columns": list(index.columns)})
    def records(pool):
        result = []
        for index in pool.values():
            refs = [number for number, per_table in fields.items()
                    if set(index.columns) <= set(per_table.get(index.table, []))]
            result.append({"schema": index.schema, "table": index.table, "columns": list(index.columns),
                "label": index.label, "estimated_bytes": estimated_index_bytes(index, tables[index.table]),
                "referenced_by_queries": refs, "generated_by_queries": sorted(generated[index.label]),
                "source_orders": source_orders[index.label]})
        return sorted(result, key=lambda r: (-len(r["referenced_by_queries"]), r["estimated_bytes"], r["label"]))
    return {"single": records(single), "suboptimal": records(composite)}


def prefix_overlap(a, b):
    if a["table"] != b["table"]:
        return False
    ac, bc = a["columns"], b["columns"]
    return ac[:len(bc)] == bc or bc[:len(ac)] == ac


def pack_control(pool, budget):
    selected, trace = [], []
    used = 0
    for record in pool:
        reason = ("over_estimated_budget" if used + record["estimated_bytes"] > budget else
                  "ordered_prefix_redundancy" if any(prefix_overlap(record, old) for old in selected) else "selected")
        trace.append({"label": record["label"], "decision": reason})
        if reason == "selected":
            selected.append(dict(record))
            used += record["estimated_bytes"]
    return selected, trace


def quote(value):
    return '"' + value.replace('"', '""') + '"'


def create_ddl(spec):
    return (f"CREATE INDEX {quote(spec['name'])} ON {quote(spec['schema'])}.{quote(spec['table'])} "
            f"USING btree ({', '.join(quote(c) for c in spec['columns'])});")


def drop_ddl(spec):
    return f"DROP INDEX {quote(spec['schema'])}.{quote(spec['name'])} RESTRICT;"


def index_name(run_id, cell_id, spec):
    return f"g9c_{run_id}_{cell_id}_{digest([spec['table'], spec['columns']])[:10]}"


def seal(plan):
    return digest({k: v for k, v in plan.items() if k != "plan_sha256"})


def validate_plan(plan, source):
    if plan.get("plan_sha256") != seal(plan):
        raise ValueError("Plan hash mismatch: regenerate and review the plan")
    if plan["database"]["database"] != TARGET or not re.fullmatch(r"[0-9a-f]{12}", plan["run_id"]):
        raise ValueError("Unexpected database or run id")
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != plan["workload_sha256"]:
        raise ValueError("Workload changed")
    if len(split_workload(source)) != 20 or plan["supported_queries"] != list(range(1, 17)):
        raise ValueError("Expected the frozen 20-query workload and 16-query subset")
    BenchmarkConfig(**plan["measurement"])
    if type(plan["rounds"]) is not int or plan["rounds"] < 1:
        raise ValueError("Rounds must be a positive integer")
    if len(plan["schedule"]) != plan["rounds"] * 12:
        raise ValueError("Incomplete strategy/budget schedule")
    if ("schedule_policy" in plan and
            plan["schedule_policy"]["fully_counterbalanced"] != (plan["rounds"] % 4 == 0)):
        raise ValueError("Schedule balance label does not match the round count")
    groups = defaultdict(list)
    names = []
    for cell in plan["schedule"]:
        groups[(cell["round"], cell["budget_mib"])].append(cell)
        if sorted(cell["query_order"]) != list(range(1, 21)):
            raise ValueError("Every cell must execute all 20 queries exactly once per iteration")
        if cell["strategy"] not in STRATEGIES or cell["budget_mib"] not in BUDGETS:
            raise ValueError("Invalid strategy/budget")
        expected = plan["configurations"][str(cell["budget_mib"])][cell["strategy"]]["indexes"]
        if [(s["table"], s["columns"]) for s in cell["indexes"]] != [(s["table"], s["columns"]) for s in expected]:
            raise ValueError("Cell differs from frozen strategy configuration")
        for spec in cell["indexes"]:
            if (spec["schema"] != "tpch" or spec["table"] not in plan["table_columns"]
                    or not 1 <= len(spec["columns"]) <= 3
                    or len(spec["columns"]) != len(set(spec["columns"]))
                    or not set(spec["columns"]) <= set(plan["table_columns"][spec["table"]])
                    or spec["name"] != index_name(plan["run_id"], cell["id"], spec)
                    or len(spec["name"].encode("utf-8")) > 63):
                raise ValueError("Invalid index specification")
            names.append(spec["name"])
        if sum(s["estimated_bytes"] for s in cell["indexes"]) > cell["budget_mib"] * MIB:
            raise ValueError("Estimated configuration exceeds its budget")
    if len(names) != len(set(names)):
        raise ValueError("Index names must be unique across cells")
    if set(groups) != {(r, b) for r in range(1, plan["rounds"] + 1) for b in BUDGETS}:
        raise ValueError("Missing round/budget groups")
    for cells in groups.values():
        if (sorted(c["strategy"] for c in cells) != sorted(STRATEGIES)
                or sorted(c["position"] for c in cells) != [1, 2, 3, 4]
                or len({tuple(c["query_order"]) for c in cells}) != 1):
            raise ValueError("Unequal strategy/query order within a block")


def build_plan(source, source3b, acceptance, environment, run_id, owner_token,
               *, seed=20261120, warmup=2, repeats=5, rounds=1, statement_timeout_ms=120000):
    require_acceptance(acceptance)
    if type(rounds) is not int or rounds < 1:
        raise ValueError("Rounds must be a positive integer")
    config = BenchmarkConfig(warmup, repeats, statement_timeout_ms)
    if not re.fullmatch(r"[0-9a-f]{12}", run_id) or not re.fullmatch(r"[0-9a-f]{32}", owner_token):
        raise ValueError("Invalid run id or ownership token")
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_hash != source3b["workload_sha256"]:
        raise ValueError("Workload differs from 3B")
    statements = split_workload(source)
    if len(statements) != 20:
        raise ValueError("Expected 20 statements")
    for statement in statements:
        validate_query(statement)
    tables = tables_from_report(source3b)
    audit, parsed, candidates = audit_advisor(source, tables)
    if not all(q["semantic_check_passed"] for q in audit):
        raise ValueError("Semantic oracle mismatch")
    recomputed = simulate(parsed.queries, tables, candidates, audit)
    for before, after in zip(source3b["budgets"], recomputed["budgets"]):
        if (before["selected_labels"] != after["selected_labels"]
                or before["estimated_selected_bytes"] != after["estimated_selected_bytes"]
                or abs(before["estimated_workload_score"] - after["estimated_workload_score"]) > 1e-6):
            raise ValueError("Current Advisor no longer reproduces frozen 3B selections")
    pools = controls(tables)
    lookup = {c["id"]: c for c in source3b["candidates"]}
    configurations = {}
    for budget, advisor in zip(BUDGETS, source3b["budgets"]):
        if advisor["budget_mib"] != budget:
            raise ValueError("3B formal budget order differs")
        configurations[str(budget)] = {"baseline": {"indexes": [], "selection_method": "no-added-indexes"}}
        for strategy in ("single", "suboptimal"):
            selected, trace = pack_control(pools[strategy], budget * MIB)
            configurations[str(budget)][strategy] = {"indexes": selected, "selection_trace": trace,
                "selection_method": "query-reference-frequency/bytes/label; prefix-overlap exclusion"}
        selected = [{k: lookup[c][k] for k in ("schema", "table", "columns", "label", "estimated_bytes")}
                    for c in advisor["selected_ids"]]
        configurations[str(budget)]["advisor"] = {"indexes": selected,
            "selection_method": advisor["selection_method"], "score": advisor["estimated_workload_score"],
            "eligible_candidate_count": advisor["eligible_candidate_count"]}
    rng = random.Random(seed)
    strategy_labels = list(STRATEGIES)
    rng.shuffle(strategy_labels)
    schedule = []
    for round_no in range(1, rounds + 1):
        budget_order = list(BUDGETS)
        rng.shuffle(budget_order)
        for budget in budget_order:
            query_order = list(range(1, 21))
            rng.shuffle(query_order)
            for position, n in enumerate(WILLIAMS[(round_no - 1) % 4], 1):
                strategy = strategy_labels[n]
                cell_id = f"r{round_no:02d}b{budget}s{position}"
                specs = []
                for original in configurations[str(budget)][strategy]["indexes"]:
                    spec = dict(original)
                    spec["name"] = index_name(run_id, cell_id, spec)
                    specs.append(spec)
                schedule.append({"id": cell_id, "round": round_no, "budget_mib": budget,
                                 "strategy": strategy, "position": position,
                                 "query_order": query_order[:], "indexes": specs})
    plan = {"schema_version": 1, "database": environment["identity"], "environment": environment,
        "run_id": run_id, "owner_token": owner_token, "ownership_tag": f"g9c:v1:{run_id}:{owner_token}",
        "seed": seed, "rounds": rounds, "measurement": asdict(config), "workload_sha256": source_hash,
        "schedule_policy": {"method": "seeded Williams rows; equal query order within each budget block",
            "fully_counterbalanced": rounds % 4 == 0,
            "limitation": "A single round has no between-round replication or four-round order balance." if rounds == 1
                          else "Only complete four-round cycles provide full Williams order balance."},
        "supported_queries": [q.number for q in parsed.queries],
        "table_columns": {n: list(t.columns) for n, t in tables.items()},
        "frozen_catalog": source3b["catalog"], "control_pools": pools,
        "expected_rows": {"orders": acceptance["orders"]["rows"], "lineitem": acceptance["lineitem"]["rows"]},
        "configurations": configurations, "schedule": schedule, "asset_hashes": asset_hashes(),
        "actual_size_policy": "strict-infeasible: rollback whole build transaction; no timing, no trim, no backfill",
        "cache_policy": "warm-cache: full-table content signature/prewarm under SHARE locks before each cell, then equal per-query warmups; no cache flush/restart",
        "data_signature_algorithm": "row-count + two seeded hashtextextended row_to_json sums; probabilistic content signature, same PG version",
        "statistics_policy": "freeze 3B selection statistics; reject column-statistics changes at runtime; do not disable auto-maintenance",
        "control_policy": "Suboptimal means unoptimized source-order, not guaranteed slower; no measured-performance selection",
        "formal_execution_authorized": False}
    plan["plan_sha256"] = seal(plan)
    validate_plan(plan, source)
    return plan


def ddl_manifest(plan):
    lines = ["-- REVIEW ONLY. Target: advisor_benchmark. Do not execute this file manually.",
             f"-- Plan SHA256: {plan['plan_sha256']}; real execution requires controller approval."]
    for cell in plan["schedule"]:
        lines.append(f"\n-- {cell['id']} {cell['strategy']} {cell['budget_mib']} MiB; one atomic build transaction")
        for spec in cell["indexes"]:
            tag = "'" + plan["ownership_tag"].replace("'", "''") + "'"
            lines.extend((create_ddl(spec), f"COMMENT ON INDEX {quote(spec['schema'])}.{quote(spec['name'])} IS {tag};",
                          "-- later cleanup ONLY after catalog identity/ownership verification: " + drop_ddl(spec)))
    return "\n".join(lines) + "\n"
