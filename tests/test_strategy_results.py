"""Analysis tests use synthetic round summaries; no PostgreSQL or DDL."""
import unittest

from analysis.strategy_results import aggregate, geometric_mean


def cell(round_number, strategy, time, status="ok"):
    result = {"id": f"r{round_number}-{strategy}", "round": round_number,
              "budget_mib": 100, "strategy": strategy, "status": status,
              "actual_mib": 0 if strategy == "baseline" else 50,
              "estimated_mib": 0 if strategy == "baseline" else 80}
    if status == "ok":
        for subset, fraction in (("full20", 1), ("advisor16", .8)):
            result.update({subset + "_execution_ms": time * fraction,
                           subset + "_hits": 10 * fraction,
                           subset + "_reads": 20 * fraction})
    return result


class ResultsTests(unittest.TestCase):
    def test_speedup_pairs_rounds_before_geometric_mean(self):
        records = [cell(1, "baseline", 100), cell(2, "baseline", 400),
                   cell(1, "advisor", 50), cell(2, "advisor", 100)]
        advisor = next(r for r in aggregate(records) if r["budget_mib"] == 100 and r["strategy"] == "advisor")
        self.assertAlmostEqual(advisor["full20_paired_speedup"], 8**.5)
        self.assertNotAlmostEqual(advisor["full20_paired_speedup"], 250 / 75)
        self.assertEqual(advisor["full20_paired_n"], 2)
        self.assertEqual(advisor["advisor16_mean_ms"], 60)

    def test_infeasible_is_missing_performance_and_storage(self):
        records = [cell(1, "baseline", 100), cell(1, "advisor", None, "budget_exceeded")]
        advisor = next(r for r in aggregate(records) if r["budget_mib"] == 100 and r["strategy"] == "advisor")
        self.assertEqual(advisor["successful_rounds"], 0)
        self.assertIsNone(advisor["actual_mib"])
        self.assertIsNone(advisor["full20_mean_ms"])
        self.assertIsNone(advisor["full20_paired_speedup"])

    def test_missing_baseline_prevents_unpaired_speedup(self):
        advisor = next(r for r in aggregate([cell(2, "advisor", 100)])
                       if r["budget_mib"] == 100 and r["strategy"] == "advisor")
        self.assertEqual(advisor["successful_rounds"], 1)
        self.assertEqual(advisor["full20_paired_n"], 0)
        self.assertIsNone(advisor["full20_paired_speedup"])

    def test_invalid_or_empty_ratios_are_not_zero_speedup(self):
        for values in ([], [0], [-1], [2, 0]):
            self.assertIsNone(geometric_mean(values))


if __name__ == "__main__":
    unittest.main()
