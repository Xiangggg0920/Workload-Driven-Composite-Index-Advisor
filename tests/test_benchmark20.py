"""Semantic checks for the frozen workload, not just a no-exception smoke test."""
import os
from pathlib import Path
import re
import unittest

import psycopg
from dotenv import load_dotenv

from advisor.parser import parse_workload
from advisor.statistics import TableStats, ColumnStats
from benchmark.runner import BenchmarkConfig, new_report, run_benchmark
from benchmark.sql import split_workload, validate_query
from workload.benchmark20_manifest import CASES
from workload.validate_benchmark20 import audit_advisor, validate

ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "workload/benchmark20.sql").read_bytes().decode("utf-8-sig")


def fixture_tables():
    """Known schema plus explicit cardinality ordering, without a live server."""
    schema = (ROOT / "dataset/schema.sql").read_text(encoding="utf-8")
    result = {}
    distinct = {"o_orderkey": 15000, "o_custkey": 1000, "o_clerk": 1000,
                "o_orderpriority": 5, "o_orderstatus": 3, "l_orderkey": 15000,
                "l_returnflag": 3, "l_linestatus": 2, "l_shipmode": 7, "l_suppkey": 100}
    for table, body in re.findall(r"CREATE TABLE tpch\.(\w+)\s*\((.*?)\);", schema, re.S):
        names = re.findall(r"^\s+([ol]_\w+)\s+", body, re.M)
        cols = {name: ColumnStats(distinct.get(name, 2500), 0, 8) for name in names}
        result[table] = TableStats("tpch", table, 15000 if table == "orders" else 60175, 2000000, cols)
    return result


class Benchmark20Tests(unittest.TestCase):
    def test_twenty_unique_read_only_statements_and_ids(self):
        statements = split_workload(SOURCE)
        self.assertEqual(len(statements), 20)
        self.assertEqual(len({s.sql for s in statements}), 20)
        self.assertEqual(re.findall(r"^-- Q(\d\d):", SOURCE, re.M), [f"{n:02d}" for n in range(1, 21)])
        for statement in statements:
            validate_query(statement)

    def test_every_supported_predicate_and_candidate_matches_manual_oracle(self):
        results, parsed, candidates = audit_advisor(SOURCE, fixture_tables())
        self.assertEqual([q.number for q in parsed.queries], list(range(1, 17)))
        self.assertEqual(len(parsed.warnings), 4)
        for result in results:
            with self.subTest(query=result["number"]):
                self.assertTrue(result["semantic_check_passed"], result)
        self.assertEqual(len(candidates), 19)

    def test_literal_left_operators_are_normalized(self):
        for operator, expected in (("=", "="), ("<", ">"), ("<=", ">="), (">", "<"), (">=", "<=")):
            with self.subTest(operator=operator):
                result = parse_workload(f"SELECT * FROM tpch.orders WHERE 10 {operator} o_totalprice",
                                        columns={"orders": {"o_totalprice"}})
                self.assertFalse(result.warnings)
                self.assertEqual(result.queries[0].predicates[0].operator, expected)

    def test_audit_detects_semantic_change_without_exception(self):
        changed = SOURCE.replace("100000 <= o_totalprice", "100000 >= o_totalprice")
        results, _, _ = audit_advisor(changed, fixture_tables())
        self.assertFalse(results[7]["semantic_check_passed"])

    def test_range_only_is_not_misreported_as_parser_failure(self):
        results, _, _ = audit_advisor(SOURCE, fixture_tables())
        for number in (8, 13):
            self.assertEqual(results[number - 1]["classification"], "parsed_without_composite_candidates")
            self.assertEqual(results[number - 1]["actual_candidates"], [])
        for number in (17, 18, 19, 20):
            self.assertEqual(results[number - 1]["classification"], "unsupported_syntax")

    def test_oracle_references_real_schema_columns_including_joins(self):
        tables = fixture_tables()
        for case in CASES:
            for schema, table, column, kind, operator in case["predicates"]:
                self.assertEqual(schema, "tpch")
                self.assertIn(column, tables[table].columns)
            for left, lc, right, rc in case["joins"]:
                self.assertIn(lc, tables[left].columns)
                self.assertIn(rc, tables[right].columns)

    def test_shared_index_and_competing_suffixes_remain_in_workload(self):
        results, _, _ = audit_advisor(SOURCE, fixture_tables())
        self.assertEqual(results[0]["actual_candidates"], results[1]["actual_candidates"])
        self.assertNotEqual(results[10]["actual_candidates"], results[11]["actual_candidates"])
        self.assertTrue(all(len(CASES[n - 1]["joins"]) == 1 for n in (14, 15, 16, 17)))


@unittest.skipUnless(os.environ.get("BENCHMARK_TEST_POSTGRES") == "1", "opt-in real PostgreSQL tests")
class Benchmark20PostgreSQLTests(unittest.TestCase):
    def test_full_workload_plans_cardinalities_semantics_and_unchanged_database(self):
        load_dotenv(ROOT / ".env")
        config = BenchmarkConfig(0, 1)
        with psycopg.connect(autocommit=True, connect_timeout=5, prepare_threshold=None) as connection:
            baseline = run_benchmark(connection, split_workload(SOURCE), new_report(SOURCE, "benchmark20.sql", config), config)
            report = validate(connection, SOURCE, baseline)
        self.assertTrue(report["passed"], [q for q in report["queries"] if not q["semantic_check_passed"]])
        self.assertEqual(baseline["summary"]["successful_queries"], 20)
        self.assertTrue(all(q["plan_alias_check_passed"] for q in report["queries"]))
        self.assertTrue(all(all(p["matching_rows"] > 0 for p in q["local_filter_selectivity"].values())
                            for q in report["queries"]))
        self.assertTrue(report["q01_q20_results_equal"])


if __name__ == "__main__":
    unittest.main()
