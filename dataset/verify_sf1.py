"""Read-only 3A acceptance gate. Does not load data, ANALYZE or create indexes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import psycopg
from dotenv import load_dotenv

from dataset.prepare_sf1 import ROOT, TARGET, EXPECTED_ROWS, protected_hashes, smoke_snapshot


def rows(connection, query):
    with connection.transaction(force_rollback=True), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = 300000")
        cursor.execute(query, binary=True, prepare=False)
        return cursor.fetchall()


def schema(connection):
    return rows(connection, "SELECT table_name,column_name,ordinal_position,data_type,"
                "character_maximum_length,numeric_precision,numeric_scale,is_nullable "
                "FROM information_schema.columns WHERE table_schema='tpch' ORDER BY table_name,ordinal_position")


def smoke_digest():
    result = {}
    with psycopg.connect(dbname="advisor_smoke", autocommit=True, connect_timeout=5) as connection:
        connection.read_only = True
        for table, keys in (("orders", "o_orderkey"), ("lineitem", "l_orderkey,l_linenumber")):
            digest = hashlib.sha256()
            data = rows(connection, f"SELECT row_to_json(t)::text FROM tpch.{table} t ORDER BY {keys}")
            for row in data:
                digest.update(row[0].encode("utf-8") + b"\n")
            result[table] = {"rows": len(data), "sha256": digest.hexdigest()}
    return result


def accept_checks(checks):
    """Every acceptance check must pass before any 3B analysis is permitted."""
    return bool(checks) and all(value is True for value in checks.values())


def verify(load_report, start_state, smoke_content_before):
    if not (load_report.get("verified") and load_report.get("data_loaded")
            and load_report.get("database_created") and load_report.get("target_database") == TARGET):
        raise ValueError("3A loader did not complete successfully; stop without retry")
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "database": TARGET,
              "scope": "3A acceptance only; no indexes and no benchmark execution"}
    with psycopg.connect(dbname="advisor_smoke", autocommit=True, connect_timeout=5) as smoke:
        smoke.read_only = True
        expected_schema = schema(smoke)
    with psycopg.connect(dbname=TARGET, autocommit=True, connect_timeout=5) as connection:
        connection.read_only = True
        report["identity"] = rows(connection, "SELECT current_database(),current_setting('transaction_read_only'),"
                                   "version(),current_setting('data_directory')")[0]
        report["schema"] = schema(connection)
        report["tables"] = rows(connection, "SELECT c.relname,c.relkind FROM pg_class c "
                                 "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='tpch' "
                                 "AND c.relkind IN ('r','p','v','m','f') ORDER BY c.relname")
        report["orders"] = dict(zip(("rows", "distinct_orderkeys", "invalid_domains", "min_date", "max_date"),
            rows(connection, "SELECT count(*),count(DISTINCT o_orderkey),"
                 "count(*) FILTER (WHERE o_orderkey<=0 OR o_custkey<=0 OR o_totalprice<0 "
                 "OR o_orderstatus NOT IN ('F','O','P') OR o_shippriority<>0),"
                 "min(o_orderdate),max(o_orderdate) FROM tpch.orders")[0]))
        report["lineitem"] = dict(zip(("rows", "invalid_domains", "min_shipdate", "max_shipdate"),
            rows(connection, "SELECT count(*),count(*) FILTER (WHERE l_orderkey<=0 OR l_partkey<=0 "
                 "OR l_suppkey<=0 OR l_linenumber NOT BETWEEN 1 AND 7 OR l_quantity NOT BETWEEN 1 AND 50 "
                 "OR l_discount NOT BETWEEN 0 AND 0.10 OR l_tax NOT BETWEEN 0 AND 0.08 "
                 "OR l_returnflag NOT IN ('A','N','R') OR l_linestatus NOT IN ('F','O')),"
                 "min(l_shipdate),max(l_shipdate) FROM tpch.lineitem")[0]))
        report["duplicate_lineitem_keys"] = rows(connection,
            "SELECT count(*) FROM (SELECT l_orderkey,l_linenumber FROM tpch.lineitem "
            "GROUP BY l_orderkey,l_linenumber HAVING count(*)>1) AS duplicates")[0][0]
        report["orphan_lineitems"] = rows(connection,
            "SELECT count(*) FROM tpch.lineitem l WHERE NOT EXISTS "
            "(SELECT 1 FROM tpch.orders o WHERE o.o_orderkey=l.l_orderkey)")[0][0]
        report["indexes"] = rows(connection, "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='tpch'")
        report["statistics"] = rows(connection, "SELECT tablename,count(*) FROM pg_stats WHERE schemaname='tpch' GROUP BY tablename ORDER BY tablename")
        report["sizes"] = rows(connection, "SELECT c.relname,pg_relation_size(c.oid),pg_total_relation_size(c.oid) "
                                "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                                "WHERE n.nspname='tpch' AND c.relkind='r' ORDER BY c.relname")
        report["database_bytes"] = rows(connection, "SELECT pg_database_size(current_database())")[0][0]
    report["smoke_after"] = smoke_snapshot()
    report["smoke_content_after"] = smoke_digest()
    report["disk_after"] = dict(zip(("total", "used", "free"), shutil.disk_usage(ROOT)))
    hashes = protected_hashes()
    for relative in start_state["protected_hashes"]:
        hashes[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    report["checks"] = {
        "target_and_read_only": report["identity"][:2] == (TARGET, "on"),
        "only_two_tables": report["tables"] == [("lineitem", "r"), ("orders", "r")],
        "schema_matches_smoke": report["schema"] == expected_schema and len(expected_schema) == 25,
        "all_columns_not_null": all(column[-1] == "NO" for column in report["schema"]),
        "orders_count": report["orders"]["rows"] == EXPECTED_ROWS["orders"],
        "lineitem_count": report["lineitem"]["rows"] == EXPECTED_ROWS["lineitem"],
        "orders_key_unique": report["orders"]["rows"] == report["orders"]["distinct_orderkeys"],
        "lineitem_key_unique": report["duplicate_lineitem_keys"] == 0,
        "lineitem_references_orders": report["orphan_lineitems"] == 0,
        "valid_domains": report["orders"]["invalid_domains"] == report["lineitem"]["invalid_domains"] == 0,
        "no_indexes": not report["indexes"],
        "analyzed_columns": report["statistics"] == [("lineitem", 16), ("orders", 9)],
        "smoke_metadata_unchanged": json.loads(json.dumps(report["smoke_after"])) == start_state["smoke_before"],
        "smoke_content_unchanged": report["smoke_content_after"] == smoke_content_before["tables"],
        "protected_files_unchanged": hashes == start_state["protected_hashes"],
        "disk_headroom": report["disk_after"]["free"] >= 10 * 1024**3,
    }
    report["passed"] = accept_checks(report["checks"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-report", type=Path, required=True)
    parser.add_argument("--start-state", type=Path, required=True)
    parser.add_argument("--smoke-before", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output exists; never overwrite acceptance evidence")
    load_dotenv(ROOT / ".env")
    inputs = [json.loads(p.read_text(encoding="utf-8")) for p in (args.load_report, args.start_state, args.smoke_before)]
    report = verify(*inputs)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"], "checks": report["checks"],
                      "database_bytes": report["database_bytes"], "free_bytes": report["disk_after"]["free"]}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
