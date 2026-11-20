import unittest

from advisor.candidates import IndexCandidate
from advisor.cost_model import ScoredCandidate
from advisor.parser import parse_workload
from advisor.statistics import TableStats, ColumnStats
from analysis.sf1_budget import FORMAL_BUDGETS_MIB, MIB, require_acceptance, selection_record, simulate


def item(name, mib, scores):
    return ScoredCandidate(IndexCandidate("tpch", "orders", (name, "date")), mib * MIB, tuple(scores))


class Sf1BudgetTests(unittest.TestCase):
    def test_acceptance_is_required_and_target_is_fixed(self):
        for report in ({}, {"passed": True, "database": "advisor_smoke", "checks": {"ok": True}},
                       {"passed": True, "database": "advisor_benchmark", "checks": {"ok": False}}):
            with self.subTest(report=report), self.assertRaises(ValueError):
                require_acceptance(report)
        require_acceptance({"passed": True, "database": "advisor_benchmark", "checks": {"ok": True}})

    def test_budget_binding_and_unmeasured_sizes_are_explicit(self):
        a, b = item("a", 60, [100, 0]), item("b", 50, [0, 90])
        ids = {a.index.label: "A", b.index.label: "B"}
        tight = selection_record([a, b], 100 * MIB, ids)
        roomy = selection_record([a, b], 120 * MIB, ids)
        self.assertEqual(tight["selected_ids"], ["A"])
        self.assertEqual(tight["estimated_workload_score"], 100)
        self.assertTrue(tight["budget_blocks_further_positive_additions"])
        self.assertEqual(roomy["estimated_workload_score"], 190)
        self.assertFalse(roomy["budget_blocks_further_positive_additions"])
        self.assertIsNone(tight["actual_index_bytes"])

    def test_zero_budget_reports_no_selection_without_division_error(self):
        a = item("a", 1, [1])
        result = selection_record([a], 0, {a.index.label: "A"})
        self.assertEqual(result["selected_ids"], [])
        self.assertEqual(result["utilization"], 0)

    def test_exact_vs_greedy_and_shortlist_metadata_are_reported(self):
        scored = [item(f"x{i}", 1, [i + 1]) for i in range(19)]
        ids = {s.index.label: f"C{i}" for i, s in enumerate(scored)}
        result = selection_record(scored, 100 * MIB, ids)
        self.assertEqual(result["selection_method"], "marginal-greedy")
        self.assertEqual(result["optimizer_candidate_count"], 19)
        self.assertFalse(result["candidate_limit_applied"])

    def test_formal_budgets_and_reference_ceiling_do_not_change(self):
        tables = {"orders": TableStats("tpch", "orders", 1000, 8192000, {
            "status": ColumnStats(3, 0, 2), "date": ColumnStats(100, 0, 4)})}
        parsed = parse_workload("SELECT * FROM tpch.orders WHERE status='F' AND date>DATE '1995-01-01'",
                                columns={"orders": {"status", "date"}})
        index = IndexCandidate("tpch", "orders", ("status", "date"))
        audit = [{"number": 1, "actual_candidates": [("orders", ("status", "date"))]}]
        result = simulate(parsed.queries, tables, [index], audit)
        self.assertEqual(tuple(b["budget_mib"] for b in result["budgets"]), FORMAL_BUDGETS_MIB)
        self.assertEqual(FORMAL_BUDGETS_MIB, (100, 500, 1024))
        self.assertEqual(result["model_score_ceiling"], result["unconstrained_heuristic_reference"]["estimated_workload_score"])
        self.assertEqual(result["candidates"][0]["generated_by_queries"], [1])
        self.assertIsNone(result["candidates"][0]["actual_index_bytes"])


if __name__ == "__main__":
    unittest.main()
