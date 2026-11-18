import unittest
from pathlib import Path
from advisor.candidates import IndexCandidate, make_candidates
from advisor.cost_model import estimated_index_bytes, score_candidates
from advisor.parser import parse_workload
from advisor.statistics import TableStats, ColumnStats

ORDER = TableStats("tpch", "orders", 15000, 1500000, {
    "o_orderkey": ColumnStats(-1,0,8),
    "o_orderstatus": ColumnStats(3,0,1),
    "o_orderdate": ColumnStats(2500,0,4),
    "o_totalprice": ColumnStats(-0.9,0,8),
})
LINE = TableStats("tpch", "lineitem", 60175, 7000000, {
    "l_orderkey": ColumnStats(15000,0,8),
    "l_shipmode": ColumnStats(7,0,10),
    "l_shipdate": ColumnStats(2500,0,4),
    "l_returnflag": ColumnStats(3,0,1),
})
TABLES = {"orders": ORDER, "lineitem": LINE}
COLS = {name: set(t.columns) for name,t in TABLES.items()}
ROOT = Path(__file__).resolve().parent.parent


class CandidateTests(unittest.TestCase):
    def test_smoke_creates_composite(self):
        parsed = parse_workload((ROOT / 'workload/smoke.sql').read_text(), columns=COLS)
        cs = make_candidates(parsed.queries, TABLES)
        self.assertIn(IndexCandidate("tpch", "orders", ("o_orderstatus", "o_orderdate")), cs)
        self.assertIn(IndexCandidate("tpch", "lineitem", ("l_shipmode", "l_shipdate")), cs)
        self.assertTrue(any(c.table == 'lineitem' and len(c.columns) >= 2 for c in cs))

    def test_column_order_equality_first(self):
        p = parse_workload("SELECT * FROM tpch.orders WHERE o_totalprice > 100 AND o_orderstatus='F';", columns=COLS)
        cs = make_candidates(p.queries, TABLES)
        self.assertEqual(cs[0].columns, ('o_orderstatus','o_totalprice'))

    def test_size_and_cost_positive_and_finite(self):
        p = parse_workload("SELECT * FROM tpch.orders WHERE o_totalprice > 100 AND o_orderstatus='F';", columns=COLS)
        c = make_candidates(p.queries, TABLES)[0]
        self.assertGreater(estimated_index_bytes(c, ORDER), 0)
        item = score_candidates([c], p.queries, TABLES)[0]
        self.assertGreater(item.independent_benefit, 0)

    def test_frequency_scales_score(self):
        sql = "SELECT * FROM tpch.orders WHERE o_totalprice > 100 AND o_orderstatus='F';"
        p1 = parse_workload(sql, columns=COLS, weights={1: 1})
        p2 = parse_workload(sql, columns=COLS, weights={1: 10})
        c = make_candidates(p1.queries, TABLES)[0]
        a = score_candidates([c], p1.queries, TABLES)[0].independent_benefit
        b = score_candidates([c], p2.queries, TABLES)[0].independent_benefit
        self.assertAlmostEqual(b, a*10)


if __name__ == '__main__':
    unittest.main()
