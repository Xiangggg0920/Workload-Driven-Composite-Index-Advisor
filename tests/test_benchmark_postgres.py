"""Opt-in real PostgreSQL tests; never create tables, indexes or other objects.

Run with BENCHMARK_TEST_POSTGRES=1 using the existing project .env.
"""
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stderr, redirect_stdout

import psycopg
from dotenv import load_dotenv

from benchmark.main import main
from benchmark.runner import BenchmarkConfig, measure_query, new_report, run_benchmark
from benchmark.sql import Statement, split_workload


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(os.environ.get("BENCHMARK_TEST_POSTGRES") == "1", "opt-in real PostgreSQL tests")
class PostgreSQLBenchmarkTests(unittest.TestCase):
    def run_source(self, source, warmup=0, repeats=2, timeout=60000):
        load_dotenv(ROOT / ".env")
        config = BenchmarkConfig(warmup, repeats, timeout)
        with psycopg.connect(autocommit=True, connect_timeout=5, prepare_threshold=None) as connection:
            report = new_report(source, "live-test.sql", config)
            return run_benchmark(connection, split_workload(source), report, config)

    def test_existing_smoke_sql(self):
        source = (ROOT / "workload/smoke.sql").read_text(encoding="utf-8")
        report = self.run_source(source, warmup=1, repeats=2)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["successful_queries"], 3)
        self.assertEqual(report["server"]["transaction_read_only"], "on")
        for query in report["queries"]:
            self.assertEqual(len(query["warmup_runs"]), 1)
            self.assertEqual(len(query["measurements"]), 2)
            for run in query["measurements"]:
                self.assertIn("Plan", run["query_plan"][0])
                self.assertGreaterEqual(run["execution_time_ms"], 0)

    def test_single_cte_and_twenty_queries(self):
        for count in (1, 20):
            source = "WITH x AS (SELECT 1 n) SELECT CASE WHEN n=1 THEN $$a;b$$ END FROM x;" * count
            report = self.run_source(source, repeats=1)
            self.assertEqual(report["summary"]["successful_queries"], count)

    def test_bad_sql_then_valid_sql_recovers(self):
        report = self.run_source("SELECT 1 +; SELECT 2", repeats=1)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["queries"][0]["measurements"][0]["error"]["sqlstate"], "42601")
        self.assertEqual(report["queries"][1]["status"], "ok")

    def test_server_read_only_rejects_locking_select(self):
        # No DML/DDL is submitted. PostgreSQL rejects row-locking SELECT in READ
        # ONLY, demonstrating server enforcement beyond a SELECT prefix check.
        report = self.run_source("SELECT * FROM tpch.orders FOR SHARE; SELECT 2", repeats=1)
        self.assertEqual(report["queries"][0]["measurements"][0]["error"]["sqlstate"], "25006")
        self.assertEqual(report["queries"][1]["status"], "ok")

    def test_timeout_then_next_query_recovers(self):
        report = self.run_source("SELECT pg_sleep(0.1); SELECT 2", repeats=1, timeout=10)
        self.assertEqual(report["queries"][0]["measurements"][0]["error"]["sqlstate"], "57014")
        self.assertEqual(report["queries"][1]["status"], "ok")

    def test_extended_protocol_rejects_second_statement(self):
        load_dotenv(ROOT / ".env")
        with psycopg.connect(autocommit=True, connect_timeout=5) as connection:
            connection.read_only = True
            # Simulate a future splitter bug with two harmless SELECTs. The
            # server must refuse the whole request rather than execute the tail.
            with self.assertRaises(psycopg.errors.SyntaxError):
                measure_query(connection, Statement("SELECT 1; SELECT 2", ("SELECT",)), BenchmarkConfig())
            result = measure_query(connection, split_workload("SELECT 3")[0], BenchmarkConfig())
            self.assertIn("query_plan", result)

    def test_percent_literals_are_not_treated_as_parameters(self):
        report = self.run_source("SELECT 'a%b' LIKE '%b'; SELECT 5 % 2", repeats=1)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["successful_queries"], 2)

    def test_cli_files_single_multiple_empty_and_error(self):
        cases = [("SELECT 1", 0, 1), ("SELECT 1; SELECT 2; SELECT 3; SELECT 4", 0, 4),
                 ("", 2, 0), ("SELECT 1 +; SELECT 2", 2, 2)]
        with TemporaryDirectory() as directory:
            for i, (source, expected_code, count) in enumerate(cases):
                with self.subTest(case=i):
                    path, output = Path(directory) / f"q{i}.sql", Path(directory) / f"q{i}.json"
                    path.write_text(source, encoding="utf-8")
                    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        code = main(["--workload", str(path), "--warmup", "0", "--repeats", "1",
                                     "--output", str(output)])
                    report = json.loads(output.read_text(encoding="utf-8"))
                    self.assertEqual(code, expected_code)
                    self.assertEqual(len(report["queries"]), count)

    def test_database_row_counts_and_indexes_unchanged(self):
        load_dotenv(ROOT / ".env")
        def snapshot():
            with psycopg.connect(autocommit=True, connect_timeout=5) as connection:
                connection.read_only = True
                with connection.transaction(force_rollback=True), connection.cursor() as cursor:
                    cursor.execute("SELECT (SELECT count(*) FROM tpch.orders), "
                                   "(SELECT count(*) FROM tpch.lineitem)")
                    counts = cursor.fetchone()
                    cursor.execute("SELECT tablename, indexname, indexdef FROM pg_indexes "
                                   "WHERE schemaname='tpch' ORDER BY tablename, indexname")
                    return counts, cursor.fetchall()
        before = snapshot()
        self.run_source((ROOT / "workload/smoke.sql").read_text(encoding="utf-8"), warmup=1)
        self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()
