"""Regression tests for issues documented in the Week 2 specification review."""
import unittest

from advisor.candidates import IndexCandidate, make_candidates
from advisor.cost_model import ScoredCandidate
from advisor.main import _budget_shortlist
from advisor.optimizer import select_indexes
from advisor.parser import parse_workload
from advisor.statistics import ColumnStats, TableStats

COLS = {
    "orders": {"o_orderkey", "o_orderstatus", "o_orderdate", "o_totalprice"},
    "lineitem": {"l_orderkey", "l_returnflag", "l_shipmode", "l_shipdate"},
}


class ParserRegressionTests(unittest.TestCase):
    def parse(self, sql):
        return parse_workload(sql, columns=COLS)

    def assert_skipped(self, sql):
        result = self.parse(sql)
        self.assertEqual(len(result.queries), 0, result)
        self.assertEqual(len(result.warnings), 1)

    def test_trailing_and_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders WHERE o_orderstatus='F' AND;")

    def test_leading_and_and_empty_parentheses_rejected(self):
        for where in ("AND o_orderstatus='F'", "()", "o_orderstatus='F' AND ()"):
            with self.subTest(where=where):
                self.assert_skipped(f"SELECT * FROM tpch.orders WHERE {where};")

    def test_simple_and_nested_parenthesized_and(self):
        for where in ("(o_orderstatus='F' AND o_orderdate>DATE '1995-01-01')",
                      "((o_orderstatus='F') AND (o_orderdate>DATE '1995-01-01'))"):
            with self.subTest(where=where):
                result = self.parse(f"SELECT * FROM tpch.orders WHERE {where};")
                self.assertFalse(result.warnings)
                self.assertEqual([(p.column, p.kind) for p in result.queries[0].predicates],
                                 [("o_orderstatus", "equality"), ("o_orderdate", "range")])

    def test_parenthesized_or_is_still_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders WHERE (o_orderstatus='F' OR o_orderstatus='O');")

    def test_multiple_inner_joins(self):
        sql = """SELECT * FROM tpch.orders o
        JOIN tpch.lineitem l ON l.l_orderkey=o.o_orderkey
        INNER JOIN tpch.orders o2 ON o2.o_orderkey=o.o_orderkey
        WHERE o.o_orderstatus='F';"""
        result = self.parse(sql)
        self.assertFalse(result.warnings)
        self.assertEqual(len(result.queries), 1)
        cols = {(p.table, p.column, p.kind) for p in result.queries[0].predicates}
        self.assertIn(("orders", "o_orderstatus", "equality"), cols)
        self.assertIn(("lineitem", "l_orderkey", "join"), cols)

    def test_join_without_on_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders o JOIN tpch.lineitem l WHERE o.o_orderstatus='F';")

    def test_join_with_empty_on_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders o JOIN tpch.lineitem l ON WHERE o.o_orderstatus='F';")

    def test_duplicate_where_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders WHERE o_orderstatus='F' WHERE o_orderkey=1;")

    def test_unrelated_three_part_schema_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders WHERE wrong.orders.o_orderstatus='F';")

    def test_correct_three_part_schema_is_supported_without_alias(self):
        result = self.parse("SELECT * FROM tpch.orders WHERE tpch.orders.o_orderstatus='F';")
        self.assertFalse(result.warnings)
        self.assertEqual(result.queries[0].predicates[0].table, "orders")

    def test_aliased_relation_disallows_base_table_qualifier(self):
        self.assert_skipped("SELECT * FROM tpch.orders o WHERE tpch.orders.o_orderstatus='F';")

    def test_self_join_unqualified_field_is_ambiguous(self):
        self.assert_skipped("SELECT * FROM tpch.orders o JOIN tpch.orders o2 "
                            "ON o.o_orderkey=o2.o_orderkey WHERE o_orderstatus='F';")

    def test_self_join_qualified_field_is_supported(self):
        result = self.parse("SELECT * FROM tpch.orders o JOIN tpch.orders o2 "
                            "ON o.o_orderkey=o2.o_orderkey WHERE o.o_orderstatus='F';")
        self.assertFalse(result.warnings)

    def test_unsupported_outer_join_is_rejected(self):
        self.assert_skipped("SELECT * FROM tpch.orders o LEFT JOIN tpch.lineitem l "
                            "ON l.l_orderkey=o.o_orderkey WHERE o.o_orderstatus='F';")

    def test_good_query_after_bad_query_is_still_parsed(self):
        result = self.parse("SELECT * FROM tpch.orders WHERE o_orderstatus='F' AND; "
                            "SELECT * FROM tpch.orders WHERE o_orderstatus='F';")
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.queries), 1)
        self.assertEqual(result.queries[0].number, 2)


class CandidateBudgetRegressionTests(unittest.TestCase):
    def test_oversize_high_frequency_cannot_hide_affordable_candidate(self):
        expensive = ScoredCandidate(IndexCandidate("tpch", "lineitem", ("l_orderkey", "l_shipdate")),
                                     2_000_000_000, (1000.0, 0.0))
        affordable = ScoredCandidate(IndexCandidate("tpch", "orders", ("o_orderstatus", "o_orderdate")),
                                      450_560, (0.0, 10.0))
        shortlisted, truncated = _budget_shortlist([expensive, affordable], 1_048_576, limit=1)
        selection = select_indexes(shortlisted, 1_048_576)
        self.assertFalse(truncated)
        self.assertEqual(selection.selected, (affordable,))
        self.assertGreater(selection.estimated_benefit, 0)

    def test_shortlist_warns_when_limited_to_feasible_candidates(self):
        x = ScoredCandidate(IndexCandidate("tpch", "orders", ("a", "b")), 100, (10.0, 0.0))
        y = ScoredCandidate(IndexCandidate("tpch", "orders", ("c", "d")), 100, (0.0, 8.0))
        shortlist, truncated = _budget_shortlist([x, y], 100, limit=1)
        self.assertTrue(truncated)
        self.assertEqual(len(shortlist), 1)
        self.assertLessEqual(select_indexes(shortlist, 100).used_bytes, 100)

    def test_unlimited_candidate_generation_keeps_low_frequency_alternative(self):
        tables = {
            "orders": TableStats("tpch", "orders", 1000, 200000, {
                "o_orderstatus": ColumnStats(3, 0, 1),
                "o_orderdate": ColumnStats(150, 0, 4),
                "o_totalprice": ColumnStats(900, 0, 8),
            }),
            "lineitem": TableStats("tpch", "lineitem", 1000000, 90000000, {
                "l_shipmode": ColumnStats(5, 0, 10),
                "l_shipdate": ColumnStats(5000, 0, 4),
            })
        }
        sql = ("SELECT * FROM tpch.lineitem WHERE l_shipmode='AIR' AND l_shipdate>DATE '1995-01-01'; "
               "SELECT * FROM tpch.orders WHERE o_orderstatus='F' AND o_orderdate>DATE '1995-01-01';")
        parsed = parse_workload(sql, columns={name: set(t.columns) for name, t in tables.items()},
                                weights={1: 1000, 2: 1})
        candidates = make_candidates(parsed.queries, tables)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].table, "lineitem")
        self.assertEqual(candidates[1].table, "orders")


if __name__ == "__main__":
    unittest.main()
