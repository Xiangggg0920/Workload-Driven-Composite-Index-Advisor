import io
import json
import sys
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from advisor.statistics import read_statistics
from advisor.main import main, render_ddl
from advisor.candidates import IndexCandidate

ROOT = Path(__file__).resolve().parent.parent


class FakeCursor:
    def __init__(self):
        self.query_log = []
        self.current = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params):
        self.query_log.append((sql, params))
        if 'FROM pg_class' in sql:
            self.current = [('orders', 15000.0, 1500000), ('lineitem', 60175.0, 7000000)]
        elif 'FROM pg_stats' in sql and params[1] == 'orders':
            self.current = [('o_orderstatus',3.0,0.0,1), ('o_orderdate',2500.0,0.0,4),
                            ('o_orderkey',-1.0,0.0,8)]
        elif 'FROM pg_stats' in sql and params[1] == 'lineitem':
            self.current = [('l_shipmode',7.0,0.0,10), ('l_shipdate',2500.0,0.0,4),
                            ('l_orderkey',15000.0,0.0,8), ('l_returnflag',3.0,0.0,1)]
        else:
            raise AssertionError(f'Unexpected SQL: {sql}')

    def fetchall(self):
        return self.current


class FakeConnection:
    def __init__(self):
        self.cur = FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self.cur


class IntegrationTests(unittest.TestCase):
    def test_read_statistics_queries_catalog_read_only(self):
        db = FakeConnection()
        result = read_statistics(db)
        self.assertEqual(set(result), {'orders','lineitem'})
        self.assertIn('o_orderdate', result['orders'].columns)
        self.assertEqual(len(db.cur.query_log), 3)
        self.assertTrue(all('SELECT' in sql for sql, _ in db.cur.query_log))
        self.assertEqual(db.cur.query_log[0][1], ('tpch',))

    def test_end_to_end_cli_with_catalog_stub(self):
        db = FakeConnection()
        mockpsycopg = types.ModuleType('psycopg')
        mockpsycopg.connect = lambda dsn='': db
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(sys.modules, {'psycopg': mockpsycopg}), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--workload', str(ROOT / 'workload/smoke.sql'), '--budget-mb', '100'])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['parsed_queries'], 3)
        self.assertEqual(result['skipped_queries'], 0)
        self.assertGreaterEqual(result['candidate_count'], 2)
        self.assertGreater(len(result['recommendations']), 0)
        self.assertLessEqual(result['estimated_selected_bytes'], result['budget_bytes'])
        self.assertTrue(all(i['ddl'].startswith('CREATE INDEX ON "tpch".') for i in result['recommendations']))

    def test_candidate_count_and_truncation_are_truthfully_reported(self):
        db = FakeConnection()
        mockpsycopg = types.ModuleType('psycopg')
        mockpsycopg.connect = lambda dsn='': db
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(sys.modules, {'psycopg': mockpsycopg}), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--workload', str(ROOT / 'workload/smoke.sql'),
                         '--budget-mb', '100', '--max-candidates', '1'])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['parsed_queries'], 3)
        self.assertGreater(result['candidate_count'], result['optimizer_candidate_count'])
        self.assertEqual(result['optimizer_candidate_count'], 1)
        self.assertTrue(result['candidate_limit_applied'])
        self.assertEqual(result['selection_method'], 'exact-within-shortlist')
        self.assertTrue(any('not globally optimal' in w for w in result['warnings']))
        self.assertLessEqual(result['estimated_selected_bytes'], result['budget_bytes'])

    def test_zero_budget_preserves_original_candidate_count(self):
        db = FakeConnection()
        mockpsycopg = types.ModuleType('psycopg')
        mockpsycopg.connect = lambda dsn='': db
        stdout = io.StringIO()
        with patch.dict(sys.modules, {'psycopg': mockpsycopg}), redirect_stdout(stdout):
            code = main(['--workload', str(ROOT / 'workload/smoke.sql'), '--budget-mb', '0'])
        self.assertEqual(code, 0)
        result = json.loads(stdout.getvalue())
        self.assertGreater(result['candidate_count'], 0)
        self.assertEqual(result['optimizer_candidate_count'], 0)
        self.assertEqual(result['recommendations'], [])
        self.assertEqual(result['estimated_selected_bytes'], 0)

    def test_identifier_quoting(self):
        index = IndexCandidate('tpch', 'orders', ('a"b', 'o_orderdate'))
        self.assertEqual(render_ddl(index), 'CREATE INDEX ON "tpch"."orders" ("a""b", "o_orderdate");')


if __name__ == '__main__':
    unittest.main()
