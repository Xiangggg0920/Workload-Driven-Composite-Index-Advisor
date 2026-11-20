"""Measure real PostgreSQL EXPLAIN ANALYZE results in rolled-back read-only transactions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
import statistics

import psycopg

from .sql import Statement, WorkloadError, validate_query


EXPLAIN = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "
METRICS = ("execution_time_ms", "planning_time_ms", "shared_hit_blocks", "shared_read_blocks")


@dataclass(frozen=True)
class BenchmarkConfig:
    warmup: int = 1
    repeats: int = 5
    statement_timeout_ms: int = 60000

    def __post_init__(self):
        for name, minimum in (("warmup", 0), ("repeats", 1), ("statement_timeout_ms", 1)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum or value > 2147483647:
                raise ValueError(f"{name} must be an integer in {minimum}..2147483647")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_report(source: str, workload: str, config: BenchmarkConfig, label: str | None = None) -> dict:
    return {
        "schema_version": 1,
        "workload": workload,
        "workload_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "label": label,
        "started_at": timestamp(),
        "finished_at": None,
        "status": "pending",
        "settings": {"warmup": config.warmup, "repeats": config.repeats,
                     "statement_timeout_ms": config.statement_timeout_ms,
                     "read_only": True, "rollback_each_attempt": True,
                     "order": "per-query warmups then measurements",
                     "explain": EXPLAIN.strip()},
        "server": None,
        "queries": [],
        "summary": {},
    }


def _configure_transaction(cursor, config: BenchmarkConfig) -> None:
    cursor.execute("SET TRANSACTION READ ONLY")
    cursor.execute("SET LOCAL standard_conforming_strings = on")
    cursor.execute(f"SET LOCAL statement_timeout = {config.statement_timeout_ms}")
    cursor.execute("SHOW transaction_read_only")
    if cursor.fetchone()[0] != "on":
        raise RuntimeError("PostgreSQL did not enable the read-only transaction")


def read_server_metadata(connection, config: BenchmarkConfig) -> dict:
    names = ("server_version", "block_size", "work_mem", "jit",
             "max_parallel_workers_per_gather", "random_page_cost",
             "effective_cache_size", "track_io_timing", "search_path")
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        _configure_transaction(cursor, config)
        cursor.execute("SELECT current_database(), " + ", ".join(
            f"current_setting('{name}')" for name in names))
        row = cursor.fetchone()
    return {"database": row[0], **dict(zip(names, row[1:])), "transaction_read_only": "on"}


def extract_metrics(payload) -> dict:
    """Use root execution counters: parent counters already include children.

    Planning buffer counters are separate, not added to execution buffer counts.
    Keep the complete server JSON array unchanged in each raw run.
    """
    if (not isinstance(payload, list) or len(payload) != 1
            or not isinstance(payload[0], dict) or not isinstance(payload[0].get("Plan"), dict)):
        raise ValueError("Unexpected EXPLAIN JSON structure")
    document = payload[0]
    root = document["Plan"]
    values = {
        "execution_time_ms": document.get("Execution Time"),
        "planning_time_ms": document.get("Planning Time"),
        "shared_hit_blocks": root.get("Shared Hit Blocks", 0),
        "shared_read_blocks": root.get("Shared Read Blocks", 0),
        "planning_shared_hit_blocks": document.get("Planning", {}).get("Shared Hit Blocks", 0),
        "planning_shared_read_blocks": document.get("Planning", {}).get("Shared Read Blocks", 0),
    }
    for name, value in values.items():
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0):
            raise ValueError(f"Missing or invalid EXPLAIN metric: {name}")
    return values


def measure_query(connection, statement: Statement, config: BenchmarkConfig) -> dict:
    # Run validation again at the execution boundary, even for API callers.
    validate_query(statement)
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        _configure_transaction(cursor, config)
        # Binary results force the single-statement extended query protocol even
        # without parameters (an empty parameter tuple alone does NOT do this).
        # No parameters also leaves literal '%' characters in SQL untouched.
        # Disable preparation so repeats don't reuse a cached plan.
        cursor.execute(EXPLAIN + statement.sql, binary=True, prepare=False)
        row = cursor.fetchone()
        if row is None:
            raise ValueError("EXPLAIN returned no JSON plan")
        payload = row[0]
        metrics = extract_metrics(payload)
    return {**metrics, "query_plan": payload}


def error_details(exc: Exception) -> dict:
    if isinstance(exc, psycopg.Error):
        # Connection errors can contain connection details; do not copy a DSN or
        # the full exception into a report. Server primary diagnostics are useful
        # for statement syntax, permission and timeout failures.
        message = exc.diag.message_primary or type(exc).__name__
        return {"type": type(exc).__name__, "sqlstate": exc.sqlstate, "message": message}
    return {"type": type(exc).__name__, "sqlstate": None, "message": str(exc)}


def summarize(runs: list[dict]) -> dict:
    successful = [run for run in runs if run["status"] == "ok"]
    result = {"successful_measurements": len(successful)}
    if successful:
        for name in METRICS:
            values = [run[name] for run in successful]
            result[name] = {"mean": statistics.fmean(values), "median": statistics.median(values),
                            "min": min(values), "max": max(values)}
    return result


def run_benchmark(connection, statements: list[Statement], report: dict,
                  config: BenchmarkConfig) -> dict:
    """One connection, fresh transaction/snapshot per attempt; never commit a query.

    On the first failed attempt, stop that query and continue the next one. This
    preserves partial measurements without retrying deterministic SQL errors.
    """
    if not connection.autocommit:
        raise ValueError("Benchmark requires an idle autocommit connection")
    connection.read_only = True
    report["server"] = read_server_metadata(connection, config)
    for number, statement in enumerate(statements, 1):
        query = {"number": number, "sql": statement.sql,
                 "sql_sha256": hashlib.sha256(statement.sql.encode("utf-8")).hexdigest(),
                 "status": "pending", "warmup_runs": [], "measurements": [], "summary": {}}
        report["queries"].append(query)
        try:
            validate_query(statement)
        except WorkloadError as exc:
            query.update(status="rejected", error=error_details(exc))
            continue
        failed = False
        for phase, count, destination in (("warmup", config.warmup, query["warmup_runs"]),
                                           ("measurement", config.repeats, query["measurements"])):
            for iteration in range(1, count + 1):
                run = {"iteration": iteration, "phase": phase, "started_at": timestamp()}
                destination.append(run)
                try:
                    run.update(measure_query(connection, statement, config))
                    run["status"] = "ok"
                except (psycopg.Error, ValueError, RuntimeError) as exc:
                    run.update(status="error", error=error_details(exc))
                    failed = True
                run["finished_at"] = timestamp()
                if failed:
                    query["failed_phase"] = phase
                    break
            if failed:
                break
        query["status"] = "error" if failed else "ok"
        query["summary"] = summarize(query["measurements"])
    queries = report["queries"]
    succeeded = sum(query["status"] == "ok" for query in queries)
    report["summary"] = {
        "query_count": len(queries), "successful_queries": succeeded,
        "failed_queries": sum(query["status"] == "error" for query in queries),
        "rejected_queries": sum(query["status"] == "rejected" for query in queries),
        "successful_measurements": sum(query["summary"].get("successful_measurements", 0) for query in queries),
    }
    report["status"] = ("empty" if not queries else "ok" if succeeded == len(queries)
                        else "partial" if succeeded else "error")
    report["finished_at"] = timestamp()
    return report
