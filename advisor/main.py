"""CLI to recommend hypothetical composite indexes without creating any."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from .candidates import make_candidates
from .cost_model import score_candidates
from .optimizer import select_indexes
from .parser import load_workload
from .statistics import read_statistics

ROOT = Path(__file__).resolve().parent.parent


def _weights(path: Path | None) -> dict[int, float] | None:
    if path is None:
        return None
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("weights JSON must be an object mapping statement number to positive frequency")
    return {int(k): float(v) for k, v in content.items()}


def _ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def render_ddl(index) -> str:
    # Quote names to avoid SQL injection, even though names originate from
    # PostgreSQL's catalog.
    table = f"{_ident(index.schema)}.{_ident(index.table)}"
    cols = ", ".join(_ident(x) for x in index.columns)
    return f"CREATE INDEX ON {table} ({cols});"


def _budget_shortlist(items, budget_bytes: int, limit: int):
    """Cap *after* estimating bytes and benefit, never by SQL frequency alone.

    This remains a heuristic shortlist if ``limit`` is reached. The optimizer
    is exact only within the shortlist, which is reported explicitly in JSON.
    """
    feasible = [x for x in items if x.estimated_bytes <= budget_bytes
                and x.independent_benefit > 0]
    if len(feasible) <= limit:
        return feasible, False
    # Greedy marginal-work-per-byte favors complementary query coverage.
    ranked = sorted(feasible, key=lambda x: x.index.label)
    selected = []
    covered = tuple(0.0 for _ in ranked[0].savings_by_query)
    while ranked and len(selected) < limit:
        def priority(item):
            gain = sum(max(0.0, new - old)
                       for new, old in zip(item.savings_by_query, covered))
            return (gain / item.estimated_bytes, gain)
        pick = min(ranked, key=lambda x: (-priority(x)[0], -priority(x)[1], x.index.label))
        selected.append(pick)
        covered = tuple(max(a, b) for a, b in zip(covered, pick.savings_by_query))
        ranked.remove(pick)
    return selected, True


def run(args) -> int:
    import psycopg
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    with psycopg.connect(args.dsn) as connection:
        tables = read_statistics(connection, schema=args.schema)
    columns = {name: set(stats.columns) for name, stats in tables.items()}
    parsed = load_workload(args.workload, schema=args.schema, columns=columns,
                           weights=_weights(args.weights))
    for warning in parsed.warnings:
        print("WARNING:", warning, file=sys.stderr)
    if not parsed.queries:
        print("No supported queries found; see warnings.", file=sys.stderr)
        return 2
    # Generate every distinct candidate first. A frequency-only truncation can
    # wrongly eliminate all affordable indexes before budget optimization.
    candidates = make_candidates(parsed.queries, tables,
                                 max_columns=args.max_columns, max_candidates=None)
    scored_all = score_candidates(candidates, parsed.queries, tables)
    budget_bytes = int(args.budget_mb * 1024 * 1024)
    scored, truncated = _budget_shortlist(scored_all, budget_bytes, args.max_candidates)
    selection = select_indexes(scored, budget_bytes)
    if truncated:
        msg = (f"Candidate shortlist limited to {args.max_candidates} affordable, "
               "positive-benefit indexes after scoring; selection is not globally optimal "
               "over all generated candidates")
        print("WARNING:", msg, file=sys.stderr)
        warnings = list(parsed.warnings) + [msg]
    else:
        warnings = list(parsed.warnings)
    result = {
        "disclaimer": "Scores and index sizes are heuristic estimates, not actual I/O, disk bytes, or milliseconds.",
        "workload": str(args.workload),
        "parsed_queries": len(parsed.queries),
        "skipped_queries": len(parsed.warnings),
        # Preserve the previous candidate_count meaning for older consumers.
        "candidate_count": len(scored_all),
        "budget_feasible_candidate_count": sum(
            x.estimated_bytes <= budget_bytes and x.independent_benefit > 0 for x in scored_all
        ),
        "optimizer_candidate_count": len(scored),
        "candidate_limit_applied": truncated,
        "budget_bytes": budget_bytes,
        "estimated_selected_bytes": selection.used_bytes,
        "estimated_workload_benefit_score": round(selection.estimated_benefit, 4),
        "selection_method": "exact-within-shortlist" if selection.exact and truncated else
                            ("exact" if selection.exact else "marginal-greedy"),
        "recommendations": [
            {"table": f"{x.index.schema}.{x.index.table}", "columns": list(x.index.columns),
             "estimated_bytes": x.estimated_bytes,
             "independent_score": round(x.independent_benefit, 4), "ddl": render_ddl(x.index)}
            for x in selection.selected
        ],
        "warnings": warnings,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, default=ROOT / "workload" / "smoke.sql")
    parser.add_argument("--budget-mb", type=float, default=100.0)
    parser.add_argument("--schema", default="tpch")
    parser.add_argument("--weights", type=Path, help="optional JSON mapping 1-based query number to frequency")
    parser.add_argument("--max-columns", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=40)
    parser.add_argument("--output", type=Path, help="save advisor JSON result here")
    parser.add_argument("--dsn", default="", help="optional psycopg connection string; otherwise use .env/libpq")
    args = parser.parse_args(argv)
    if not 0 <= args.budget_mb <= 1000000 or not 2 <= args.max_columns <= 8 or not 1 <= args.max_candidates <= 200:
        parser.error("budget-mb must be 0..1,000,000; max-columns 2..8; max-candidates 1..200")
    try:
        return run(args)
    except (ValueError, RuntimeError, OSError) as exc:
        print("Advisor error:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
