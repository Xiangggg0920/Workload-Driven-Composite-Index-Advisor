"""3A: inspect by default; generate/create/load SF1 only with an explicit execution gate.

No index management, Advisor changes or benchmark execution. Never targets smoke
for writes, never edits .env and never drops/reuses an existing target database.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import importlib.metadata
import ipaddress
import json
from pathlib import Path
import shutil
import sys

import duckdb
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from dotenv import load_dotenv

from dataset import tpch


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dataset/data/sf1"
TARGET = "advisor_benchmark"
SMOKE = "advisor_smoke"
GIB = 1024 ** 3
EXPECTED_ROWS = {"orders": 1500000, "lineitem": 6001215}
EXPECTED_COLUMNS = {"orders": 9, "lineitem": 16}


def read_rows(connection, query, params=None):
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = 60000")
        cursor.execute(query, params, prepare=False)
        return cursor.fetchall()


def smoke_snapshot():
    with psycopg.connect(dbname=SMOKE, autocommit=True, connect_timeout=5) as connection:
        connection.read_only = True
        return {
            "counts": read_rows(connection, "SELECT (SELECT count(*) FROM tpch.orders),"
                                "(SELECT count(*) FROM tpch.lineitem)")[0],
            "columns": read_rows(connection, "SELECT table_name,column_name,data_type,is_nullable "
                                 "FROM information_schema.columns WHERE table_schema='tpch' "
                                 "ORDER BY table_name,ordinal_position"),
            "indexes": read_rows(connection, "SELECT tablename,indexname,indexdef FROM pg_indexes "
                                 "WHERE schemaname='tpch' ORDER BY tablename,indexname"),
        }


def protected_hashes():
    paths = [ROOT / "workload/benchmark20.sql", ROOT / "dataset/schema.sql", ROOT / "dataset/tpch.py"]
    for directory in ("advisor", "benchmark"):
        paths.extend(sorted((ROOT / directory).glob("*.py")))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def check_space(paths, minimum):
    result = {}
    for path in paths:
        # Check the volume, not protected PostgreSQL directory contents. The
        # initial environment inspection separately checked data/WAL placement.
        volume = Path(path).anchor
        if volume not in result:
            usage = shutil.disk_usage(volume)
            result[volume] = {"total_bytes": usage.total, "free_bytes": usage.free,
                              "minimum_free_bytes": minimum, "sufficient": usage.free >= minimum}
    return result


def preflight():
    with psycopg.connect(dbname="postgres", autocommit=True, connect_timeout=5) as connection:
        connection.read_only = True
        info = read_rows(connection, "SELECT current_user,inet_server_addr()::text,inet_server_port(),"
                         "pg_is_in_recovery(),current_setting('server_version'),current_setting('data_directory')")[0]
        role = read_rows(connection, "SELECT rolsuper,rolcreatedb FROM pg_roles WHERE rolname=current_user")[0]
        exists = bool(read_rows(connection, "SELECT 1 FROM pg_database WHERE datname=%s", (TARGET,)))
        locale = read_rows(connection, "SELECT pg_encoding_to_char(encoding),datcollate,datctype,datlocprovider "
                           "FROM pg_database WHERE datname=%s", (SMOKE,))[0]
        spaces = read_rows(connection, "SELECT spcname,pg_tablespace_location(oid) FROM pg_tablespace ORDER BY spcname")
        wal = read_rows(connection, "SELECT current_setting('wal_level'),current_setting('archive_mode'),"
                        "current_setting('max_wal_size'),(SELECT count(*) FROM pg_replication_slots)")[0]
    # LOAD only uses the cached extension. No INSTALL or dbgen in inspection.
    with duckdb.connect(":memory:", config={"extension_directory": str(ROOT / "dataset/data/.duckdb-extensions"),
                                           "memory_limit": "1GB", "threads": "2"}) as generator:
        generator.execute("LOAD tpch")
        extension = generator.execute("SELECT loaded,installed FROM duckdb_extensions() WHERE extension_name='tpch'").fetchone()
    address = info[1].split("/")[0] if info[1] else ""
    local = bool(address) and ipaddress.ip_address(address).is_loopback
    disks = check_space((ROOT, Path(info[5])), 20 * GIB)
    blockers = []
    for blocked, reason in (
        (not local, "Expected the inspected local PostgreSQL server"),
        (info[3], "Server is in recovery"),
        (not any(role), "Current role cannot create a database"),
        (exists, "advisor_benchmark already exists; it will never be reused or overwritten"),
        (SOURCE.exists(), "SF1 output already exists; it will never be overwritten"),
        (locale[0] != "UTF8" or locale[3] != "c", "Expected smoke UTF8/libc locale"),
        (any(not item["sufficient"] for item in disks.values()), "Need at least 20 GiB free on each involved volume"),
        (not extension or not all(extension), "Cached TPC-H extension is unavailable"),
        (wal[1] != "off" or wal[3] != 0, "Review WAL archiving/replication retention before loading"),
    ):
        if blocked:
            blockers.append(reason)
    return {
        "inspected_at": datetime.now(timezone.utc).isoformat(),
        "mode": "inspection_only", "target_database": TARGET, "target_exists": exists,
        "source_directory": str(SOURCE), "expected_rows": EXPECTED_ROWS,
        "server": dict(zip(("role", "address", "port", "in_recovery", "version", "data_directory"), info)),
        "can_create_database": any(role), "smoke_locale": list(locale), "tablespaces": spaces,
        "wal": dict(zip(("wal_level", "archive_mode", "max_wal_size", "replication_slots"), wal)),
        "disks": disks,
        "dependencies": {name: importlib.metadata.version(name) for name in ("duckdb", "psycopg", "python-dotenv")},
        "cached_tpch_load_verified": bool(extension and all(extension)),
        "smoke_before": smoke_snapshot(), "protected_hashes": protected_hashes(),
        "blockers": blockers, "ready_for_approval": not blockers,
        "database_created": False, "sf1_generated": False, "data_loaded": False,
    }


def validate_csv(source):
    """Check scale/shape before CREATE DATABASE; keep provenance for the load."""
    result = {}
    for table, expected in EXPECTED_ROWS.items():
        path = source / f"{table}.csv"
        count = 0
        with path.open("r", encoding="utf-8", newline="") as stream:
            for row in csv.reader(stream, strict=True):
                count += 1
                if len(row) != EXPECTED_COLUMNS[table]:
                    raise ValueError(f"Invalid column count in {table}, row {count}")
        if count != expected:
            raise ValueError(f"Wrong scale: {table} has {count} rows, expected {expected}")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result[table] = {"rows": count, "bytes": path.stat().st_size, "sha256": digest.hexdigest()}
    return result


def create_target(plan):
    with psycopg.connect(dbname="postgres", autocommit=True, connect_timeout=5) as connection:
        # Recheck after generation; a concurrent database creation must abort,
        # never turn into an import into somebody else's database.
        if read_rows(connection, "SELECT 1 FROM pg_database WHERE datname=%s", (TARGET,)):
            raise RuntimeError("Target appeared during generation; refusing to use it")
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {} WITH TEMPLATE template0 ENCODING {} "
                                   "LOCALE_PROVIDER libc LC_COLLATE {} LC_CTYPE {}").format(
                sql.Identifier(TARGET), sql.Literal(plan["smoke_locale"][0]),
                sql.Literal(plan["smoke_locale"][1]), sql.Literal(plan["smoke_locale"][2])))


def verify_target():
    with psycopg.connect(dbname=TARGET, autocommit=True, connect_timeout=5) as connection:
        connection.read_only = True
        identity = read_rows(connection, "SELECT current_database()")[0][0]
        counts = read_rows(connection, "SELECT (SELECT count(*) FROM tpch.orders),"
                           "(SELECT count(*) FROM tpch.lineitem)")[0]
        indexes = read_rows(connection, "SELECT indexname FROM pg_indexes WHERE schemaname='tpch'")
        stats = read_rows(connection, "SELECT tablename,count(*) FROM pg_stats WHERE schemaname='tpch' "
                          "GROUP BY tablename ORDER BY tablename")
        sizes = read_rows(connection, "SELECT c.relname,pg_relation_size(c.oid),pg_total_relation_size(c.oid) "
                          "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                          "WHERE n.nspname='tpch' AND c.relkind='r' ORDER BY c.relname")
        dates = read_rows(connection, "SELECT min(o_orderdate),max(o_orderdate) FROM tpch.orders")
    if (identity != TARGET or tuple(counts) != tuple(EXPECTED_ROWS.values()) or indexes
            or dict(stats) != EXPECTED_COLUMNS):
        raise RuntimeError("Post-load identity/count/index/statistics verification failed")
    return {"database": identity, "counts": counts, "indexes": indexes,
            "statistics_columns": stats, "sizes": sizes, "orderdate_range": dates}


def execute_plan(plan, confirmation):
    if confirmation != TARGET:
        raise ValueError("Execution requires --confirm-database advisor_benchmark after user approval")
    if plan["blockers"]:
        raise RuntimeError("Preflight has blockers; no generation or database creation allowed")
    plan["mode"] = "approved_execution"
    with redirect_stdout(sys.stderr):
        tpch.generate(Decimal("1"), SOURCE)
    plan["sf1_generated"] = True
    plan["csv"] = validate_csv(SOURCE)
    if smoke_snapshot() != plan["smoke_before"]:
        raise RuntimeError("Smoke changed before creation; stop for review")
    disks = check_space((ROOT, Path(plan["server"]["data_directory"])), 10 * GIB)
    if any(not item["sufficient"] for item in disks.values()):
        raise RuntimeError("Need at least 10 GiB free before database creation/load")
    create_target(plan)
    plan["database_created"] = True
    # dbname explicitly overrides PGDATABASE from .env; never changes .env or
    # process PGDATABASE. Existing schema/COPY/ANALYZE logic is reused unchanged.
    with redirect_stdout(sys.stderr):
        tpch.load(SOURCE, make_conninfo(dbname=TARGET))
    plan["data_loaded"] = True
    plan["target_verification"] = verify_target()
    plan["smoke_after"] = smoke_snapshot()
    if plan["smoke_after"] != plan["smoke_before"] or protected_hashes() != plan["protected_hashes"]:
        raise RuntimeError("Smoke/protected-file verification changed; stop for review")
    plan["verified"] = True
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="generate/create/load; only after user approval")
    parser.add_argument("--confirm-database", help="execution gate; must exactly equal advisor_benchmark")
    parser.add_argument("--output", type=Path, help="save a NEW JSON report; never overwrite")
    args = parser.parse_args(argv)
    if args.execute and args.confirm_database != TARGET:
        parser.error("--execute requires --confirm-database advisor_benchmark")
    if args.confirm_database and not args.execute:
        parser.error("--confirm-database requires --execute")
    if args.output and args.output.exists():
        parser.error("Output already exists")
    load_dotenv(ROOT / ".env")
    report = {}
    code = 0
    try:
        report = preflight()
        if args.execute:
            execute_plan(report, args.confirm_database)
        elif report["blockers"]:
            code = 2
    except (psycopg.Error, duckdb.Error, OSError, ValueError, RuntimeError, csv.Error) as exc:
        message = (exc.diag.message_primary or type(exc).__name__) if isinstance(exc, psycopg.Error) else str(exc)
        report["error"] = type(exc).__name__ + ": " + message
        report["verified"] = False
        code = 2
    payload = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    print(payload, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
