"""Run a SQL workload through PostgreSQL EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import psycopg
from dotenv import load_dotenv

from .runner import BenchmarkConfig, error_details, new_report, run_benchmark, timestamp
from .sql import WorkloadError, split_workload


ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, default=ROOT / "workload" / "smoke.sql")
    parser.add_argument("--warmup", type=int, default=1, help="warmup attempts per query (default: 1)")
    parser.add_argument("--repeats", type=int, default=5, help="measured attempts per query (default: 5)")
    parser.add_argument("--statement-timeout-ms", type=int, default=60000)
    parser.add_argument("--connect-timeout", type=int, default=5, help="connection timeout in seconds")
    parser.add_argument("--dsn", default="", help="otherwise use project .env / libpq environment")
    parser.add_argument("--label", help="optional experiment label; does not change database state")
    parser.add_argument("--output", type=Path, help="also save JSON to a NEW file; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        config = BenchmarkConfig(args.warmup, args.repeats, args.statement_timeout_ms)
        if not 1 <= args.connect_timeout <= 2147483647:
            raise ValueError("connect-timeout must be a positive 32-bit integer")
    except ValueError as exc:
        parser.error(str(exc))
    # Check before connecting so a filename mistake never triggers a benchmark.
    if args.output and args.output.exists():
        print(f"Benchmark error: output already exists: {args.output}", file=sys.stderr)
        return 2
    report = new_report("", str(args.workload), config, args.label)
    try:
        # Keep CR/LF inside SQL literals unchanged (read_text normalizes them).
        source = args.workload.read_bytes().decode("utf-8-sig")
        report = new_report(source, str(args.workload), config, args.label)
        statements = split_workload(source)
        if not statements:
            raise WorkloadError("Workload contains no SQL queries")
        load_dotenv(ROOT / ".env")
        with psycopg.connect(args.dsn, autocommit=True, connect_timeout=args.connect_timeout,
                             prepare_threshold=None, application_name="group9_benchmark") as connection:
            run_benchmark(connection, statements, report, config)
    except (psycopg.Error, OSError, UnicodeError, ValueError, RuntimeError) as exc:
        report.update(status="error", error=error_details(exc), finished_at=timestamp())
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        except OSError as exc:
            print(f"Benchmark output error: {exc}", file=sys.stderr)
            print(payload, end="")
            return 2
    print(payload, end="")
    if report["status"] != "ok":
        print("Benchmark did not complete successfully; see JSON errors and raw runs.", file=sys.stderr)
        return 2
    return 0
