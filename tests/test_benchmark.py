import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stderr, redirect_stdout, contextmanager
from unittest.mock import patch

import psycopg

from benchmark.main import main
from benchmark.runner import (BenchmarkConfig, EXPLAIN, extract_metrics, new_report,
                              run_benchmark, summarize)
from benchmark.sql import WorkloadError, split_workload, validate_query


PLAN = [{"Plan": {"Node Type": "Aggregate", "Shared Hit Blocks": 12, "Shared Read Blocks": 3,
                  "Plans": [{"Node Type": "Seq Scan", "Shared Hit Blocks": 12, "Shared Read Blocks": 3}]},
         "Planning": {"Shared Hit Blocks": 7, "Shared Read Blocks": 1},
         "Planning Time": 0.2, "Execution Time": 1.5}]


class FakeConnection:
    """Only the runner's transaction control and EXPLAIN protocol, no SQL engine."""
    autocommit = True
    read_only = False

    def __init__(self, fail_at=None):
        self.log = []
        self.active = False
        self.row = None
        self.attempts = 0
        self.rollbacks = 0
        self.fail_at = fail_at

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @contextmanager
    def transaction(self, *, force_rollback):
        if not self.read_only or not force_rollback or self.active:
            raise AssertionError("Expected a fresh read-only rollback transaction")
        self.active = True
        self.configured = False
        try:
            yield
        finally:
            self.active = False
            self.rollbacks += 1

    @contextmanager
    def cursor(self):
        yield self

    def execute(self, sql, params=None, **kwargs):
        self.log.append((sql, params, kwargs))
        if not self.active:
            raise AssertionError("SQL outside a transaction")
        if sql == "SET TRANSACTION READ ONLY":
            self.configured = True
        elif sql.startswith("SET LOCAL "):
            pass
        elif sql == "SHOW transaction_read_only":
            self.row = ("on",)
        elif sql.startswith("SELECT current_database()"):
            self.row = ("test_db", "17.12", "8192", "4MB", "on", "2", "4", "4GB", "off", "public")
        elif sql.startswith(EXPLAIN):
            if not self.configured or params is not None or kwargs != {"prepare": False, "binary": True}:
                raise AssertionError("EXPLAIN must use protected single-statement execution")
            self.attempts += 1
            if self.attempts == self.fail_at or "broken" in sql:
                raise psycopg.errors.SyntaxError("simulated syntax error")
            self.row = (copy.deepcopy(PLAN),)
        else:
            raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchone(self):
        return self.row


class WorkloadSplitterTests(unittest.TestCase):
    def test_one_and_missing_final_semicolon(self):
        self.assertEqual([s.sql for s in split_workload("SELECT 1")], ["SELECT 1"])

    def test_arbitrary_count_including_twenty_queries(self):
        for count in (1, 4, 20, 27):
            with self.subTest(count=count):
                self.assertEqual(len(split_workload("SELECT 1;" * count)), count)

    def test_empty_comments_and_empty_statements(self):
        for source in ("", " \n", ";;;", "-- hi;\n/* outer /* inner; */ done */;"):
            self.assertEqual(split_workload(source), [])

    def test_semicolons_in_strings_names_and_comments(self):
        source = '-- hi;\nSELECT \'a;it\'\'s\' AS "a;""b"; /* c; */ SELECT 2;'
        statements = split_workload(source)
        self.assertEqual(len(statements), 2)
        self.assertIn("'a;it''s'", statements[0].sql)
        self.assertIn('"a;""b"', statements[0].sql)

    def test_escaped_strings(self):
        source = r"SELECT E'a\';b'; SELECT E'c\\'; SELECT 3;"
        self.assertEqual(len(split_workload(source)), 3)

    def test_ordinary_backslash_does_not_escape_quote(self):
        self.assertEqual(len(split_workload("SELECT '\\'; SELECT 2;")), 2)

    def test_dollar_quotes_and_identifier_dollars(self):
        source = "SELECT $$a;b$$; SELECT $tag$a;'b$tag$; SELECT 1 AS foo$bar;"
        self.assertEqual(len(split_workload(source)), 3)

    def test_nested_comments_and_bom(self):
        self.assertEqual(len(split_workload("\ufeff/* a /* ; */ b */ SELECT 1;")), 1)

    def test_cr_comments_and_crlf_inside_literals_preserved(self):
        source = "-- comment;\rSELECT 'a\r\nb';\rSELECT 2"
        statements = split_workload(source)
        self.assertEqual(len(statements), 2)
        self.assertIn("'a\r\nb'", statements[0].sql)

    def test_unterminated_constructs_rejected(self):
        for source in ("SELECT 'a", 'SELECT "a', "SELECT $$a", "/* a", "SELECT E'a\\"):
            with self.subTest(source=source), self.assertRaises(WorkloadError):
                split_workload(source)

    def test_cte_subquery_case_and_literals_accepted(self):
        for sql in ("WITH a AS (SELECT 1) SELECT * FROM a",
                    "SELECT CASE WHEN true THEN 'DELETE' ELSE 'SET' END",
                    'SELECT 1 AS "UPDATE"', "VALUES (1), (2)", "TABLE tpch.orders",
                    "SELECT * FROM (SELECT 1) a"):
            validate_query(split_workload(sql)[0])

    def test_write_cte_select_into_and_control_rejected(self):
        for sql in ("DELETE FROM tpch.orders", "SELECT * INTO TEMP t FROM tpch.orders",
                    "WITH x AS (DELETE FROM tpch.orders RETURNING *) SELECT * FROM x",
                    "CREATE INDEX x ON tpch.orders(o_orderkey)", "COMMIT", "SET transaction_read_only=off"):
            with self.subTest(sql=sql), self.assertRaises(WorkloadError):
                validate_query(split_workload(sql)[0])


class BenchmarkRunnerTests(unittest.TestCase):
    def run_source(self, source="SELECT 1", config=None, db=None):
        config = config or BenchmarkConfig(warmup=1, repeats=3)
        db = db or FakeConnection()
        report = new_report(source, "memory.sql", config)
        return run_benchmark(db, split_workload(source), report, config), db

    def test_all_raw_runs_plans_and_warmup_exclusion(self):
        report, db = self.run_source()
        query = report["queries"][0]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(query["warmup_runs"]), 1)
        self.assertEqual(len(query["measurements"]), 3)
        self.assertEqual(query["summary"]["successful_measurements"], 3)
        self.assertEqual(db.attempts, 4)
        for run in query["warmup_runs"] + query["measurements"]:
            self.assertEqual(run["query_plan"], PLAN)
            self.assertEqual(run["execution_time_ms"], 1.5)
            self.assertEqual(run["planning_time_ms"], 0.2)

    def test_root_buffers_not_sum_of_plan_nodes_or_planning(self):
        metrics = extract_metrics(PLAN)
        self.assertEqual(metrics["shared_hit_blocks"], 12)
        self.assertEqual(metrics["shared_read_blocks"], 3)
        self.assertEqual(metrics["planning_shared_hit_blocks"], 7)

    def test_no_table_buffers_default_to_zero(self):
        result = extract_metrics([{"Plan": {"Node Type": "Result"},
                                   "Execution Time": 0.1, "Planning Time": 0.05}])
        self.assertEqual(result["shared_read_blocks"], 0)
        self.assertEqual(result["shared_hit_blocks"], 0)

    def test_bad_plan_and_missing_metrics_rejected(self):
        for payload in (None, [], [{}], [{"Plan": {}}],
                        [{"Plan": {}, "Execution Time": float("nan"), "Planning Time": 0}]):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                extract_metrics(payload)

    def test_every_attempt_has_fresh_read_only_rollback_transaction(self):
        report, db = self.run_source("SELECT 1; SELECT 2")
        self.assertEqual(db.rollbacks, 9)  # metadata + two queries * (1 + 3)
        self.assertEqual(sum(sql == "SET TRANSACTION READ ONLY" for sql, _, _ in db.log), 9)
        self.assertEqual(report["server"]["transaction_read_only"], "on")

    def test_zero_warmup(self):
        report, db = self.run_source(config=BenchmarkConfig(0, 2))
        self.assertEqual(report["queries"][0]["warmup_runs"], [])
        self.assertEqual(db.attempts, 2)

    def test_twenty_queries_execute_without_special_case(self):
        report, db = self.run_source("SELECT 1;" * 20, BenchmarkConfig(0, 1))
        self.assertEqual(report["summary"]["successful_queries"], 20)
        self.assertEqual(db.attempts, 20)

    def test_error_query_does_not_poison_next_query(self):
        report, db = self.run_source("SELECT broken; SELECT 2", BenchmarkConfig(0, 2))
        self.assertEqual(report["status"], "partial")
        self.assertEqual([q["status"] for q in report["queries"]], ["error", "ok"])
        self.assertEqual(report["queries"][0]["measurements"][0]["error"]["sqlstate"], "42601")
        self.assertEqual(db.attempts, 3)

    def test_warmup_error_stops_that_query(self):
        report, db = self.run_source(db=FakeConnection(fail_at=1))
        self.assertEqual(report["queries"][0]["failed_phase"], "warmup")
        self.assertEqual(report["queries"][0]["measurements"], [])
        self.assertEqual(db.attempts, 1)

    def test_partial_measurements_preserved(self):
        report, _ = self.run_source(config=BenchmarkConfig(0, 5), db=FakeConnection(fail_at=3))
        query = report["queries"][0]
        self.assertEqual(query["status"], "error")
        self.assertEqual(len(query["measurements"]), 3)
        self.assertEqual(query["summary"]["successful_measurements"], 2)

    def test_write_rejected_without_explain_and_next_query_runs(self):
        report, db = self.run_source("WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x; SELECT 2",
                                     BenchmarkConfig(0, 1))
        self.assertEqual([q["status"] for q in report["queries"]], ["rejected", "ok"])
        self.assertEqual(db.attempts, 1)

    def test_non_autocommit_connection_rejected(self):
        db = FakeConnection()
        db.autocommit = False
        with self.assertRaises(ValueError):
            self.run_source(db=db)
        self.assertEqual(db.log, [])

    def test_read_only_verification_failure_stops_before_explain(self):
        db = FakeConnection()
        execute = db.execute
        def unsafe_setting(sql, *args, **kwargs):
            execute(sql, *args, **kwargs)
            if sql == "SHOW transaction_read_only":
                db.row = ("off",)
        db.execute = unsafe_setting
        with self.assertRaisesRegex(RuntimeError, "read-only"):
            self.run_source(db=db)
        self.assertEqual(db.attempts, 0)

    def test_config_validation(self):
        for kwargs in ({"warmup": -1}, {"repeats": 0}, {"statement_timeout_ms": 0},
                       {"warmup": True}, {"repeats": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                BenchmarkConfig(**kwargs)

    def test_summary_uses_only_successful_measurements(self):
        runs = [{"status": "ok", **{name: x for name in ("execution_time_ms", "planning_time_ms",
                 "shared_hit_blocks", "shared_read_blocks")}} for x in (1, 3)]
        result = summarize(runs + [{"status": "error"}])
        self.assertEqual(result["execution_time_ms"], {"mean": 2, "median": 2, "min": 1, "max": 3})


class BenchmarkCliTests(unittest.TestCase):
    def invoke(self, source, extra=(), *, connection=None):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "queries.sql"
            path.write_text(source, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with patch("benchmark.main.psycopg.connect", return_value=connection or FakeConnection()) as connect:
                with redirect_stdout(out), redirect_stderr(err):
                    code = main(["--workload", str(path), "--warmup", "0", "--repeats", "1", *extra])
            return code, json.loads(out.getvalue()), connect

    def test_cli_json_and_connection_options(self):
        code, report, connect = self.invoke("SELECT 1; SELECT 2")
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["query_count"], 2)
        self.assertTrue(connect.call_args.kwargs["autocommit"])
        self.assertIsNone(connect.call_args.kwargs["prepare_threshold"])
        self.assertNotIn("dsn", report)

    def test_empty_file_fails_without_connecting(self):
        code, report, connect = self.invoke("-- only comments")
        self.assertEqual(code, 2)
        self.assertIn("no SQL", report["error"]["message"])
        connect.assert_not_called()

    def test_unterminated_file_fails_without_connecting(self):
        code, report, connect = self.invoke("SELECT 'unterminated")
        self.assertEqual(code, 2)
        self.assertEqual(report["error"]["type"], "WorkloadError")
        connect.assert_not_called()

    def test_query_errors_return_nonzero_and_partial_json(self):
        code, report, _ = self.invoke("SELECT broken; SELECT 2")
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "partial")

    def test_new_output_contains_same_json(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "new" / "result.json"
            code, report, _ = self.invoke("SELECT 1", ["--output", str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)

    def test_existing_output_never_overwritten_or_connected(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "keep.json"
            output.write_text("keep", encoding="utf-8")
            with patch("benchmark.main.psycopg.connect") as connect:
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(["--output", str(output)]), 2)
            connect.assert_not_called()
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_connection_error_is_json_without_traceback_or_dsn(self):
        with patch("benchmark.main.psycopg.connect", side_effect=psycopg.OperationalError("secret DSN")):
            with redirect_stdout(out := io.StringIO()), redirect_stderr(io.StringIO()):
                code = main([])
        self.assertEqual(code, 2)
        self.assertNotIn("secret DSN", out.getvalue())
        self.assertEqual(json.loads(out.getvalue())["error"]["type"], "OperationalError")

    def test_invalid_counts_exit_before_connecting(self):
        for args in (["--warmup", "-1"], ["--repeats", "0"], ["--statement-timeout-ms", "0"]):
            with patch("benchmark.main.psycopg.connect") as connect:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    main(args)
            self.assertEqual(exc.exception.code, 2)
            connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
