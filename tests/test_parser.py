import unittest
from pathlib import Path
from advisor.parser import parse_workload, split_statements

ROOT = Path(__file__).resolve().parent.parent
COLS = {
    "orders": {"o_orderkey", "o_orderstatus", "o_orderdate", "o_totalprice", "o_orderpriority"},
    "lineitem": {"l_orderkey", "l_shipmode", "l_shipdate", "l_returnflag", "l_linestatus"},
}


class ParserTests(unittest.TestCase):
    def test_smoke_sql_three_queries(self):
        parsed = parse_workload((ROOT / 'workload/smoke.sql').read_text(), columns=COLS)
        self.assertFalse(parsed.warnings, parsed.warnings)
        self.assertEqual(len(parsed.queries), 3)
        self.assertEqual([(p.table, p.column, p.kind) for p in parsed.queries[0].predicates], [
            ('orders', 'o_orderstatus', 'equality'),
            ('orders', 'o_orderdate', 'range'),
            ('orders', 'o_orderdate', 'range')
        ])
        self.assertTrue(any(p.table == 'lineitem' and p.column == 'l_orderkey' and p.kind == 'join'
                            for p in parsed.queries[2].predicates))

    def test_quoted_semicolon_and_sql_comments(self):
        text = "-- comment ;\nSELECT * FROM tpch.orders WHERE o_orderstatus='F;X'; /* a; */ SELECT * FROM tpch.orders WHERE o_totalprice > 4;"
        parsed = parse_workload(text, columns=COLS)
        self.assertEqual(len(parsed.queries), 2)
        self.assertFalse(parsed.warnings)
        self.assertEqual(len(split_statements(text)), 2)

    def test_unqualified_column_in_join_resolves_catalog(self):
        sql = "SELECT * FROM tpch.orders o JOIN tpch.lineitem l ON l.l_orderkey=o.o_orderkey WHERE o_orderstatus='F' AND l_returnflag='R';"
        p = parse_workload(sql, columns=COLS)
        self.assertFalse(p.warnings, p.warnings)
        self.assertIn(('orders', 'o_orderstatus'), [(x.table, x.column) for x in p.queries[0].predicates])

    def test_or_skipped_safely(self):
        p = parse_workload("SELECT * FROM tpch.orders WHERE (o_orderstatus='F' OR o_orderstatus='O');", columns=COLS)
        self.assertEqual(len(p.queries), 0)
        self.assertIn('OR', p.warnings[0])

    def test_invalid_query_and_subquery_skipped(self):
        p = parse_workload("DELETE FROM tpch.orders; SELECT * FROM tpch.orders WHERE o_orderkey IN (SELECT o_orderkey FROM tpch.orders);", columns=COLS)
        self.assertEqual(len(p.queries), 0)
        self.assertEqual(len(p.warnings), 2)

    def test_query_frequency(self):
        p = parse_workload("SELECT * FROM tpch.orders WHERE o_orderstatus='F';", weights={1: 12.0}, columns=COLS)
        self.assertEqual(p.queries[0].weight, 12.0)


if __name__ == '__main__':
    unittest.main()
