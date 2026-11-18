import unittest
from advisor.candidates import IndexCandidate
from advisor.cost_model import ScoredCandidate
from advisor.optimizer import select_indexes


def make(name, size, scores):
    return ScoredCandidate(IndexCandidate('tpch', 'orders', (name, 'o_orderdate')), size, tuple(scores))


class OptimizerTests(unittest.TestCase):
    def test_budget_is_hard_limit(self):
        a, b = make('a', 10, [10]), make('b', 15, [11])
        s = select_indexes([a,b], 15)
        self.assertLessEqual(s.used_bytes, 15)
        self.assertEqual(s.selected, (b,))

    def test_overlap_not_double_counted(self):
        a, b = make('a', 10, [20, 0]), make('b', 10, [20, 0])
        s = select_indexes([a,b], 20)
        self.assertEqual(len(s.selected), 1)
        self.assertEqual(s.estimated_benefit, 20)

    def test_complementary_indexes(self):
        a, b = make('a', 10, [20, 0]), make('b', 10, [0, 20])
        s = select_indexes([a,b], 20)
        self.assertEqual(len(s.selected), 2)
        self.assertEqual(s.estimated_benefit, 40)

    def test_zero_budget(self):
        s = select_indexes([make('a', 10, [20])], 0)
        self.assertEqual(s.estimated_benefit, 0)
        self.assertEqual(s.selected, ())

    def test_greedy_fallback(self):
        items = [make(f'x{i}', 10, [i+1]) for i in range(18)]
        s = select_indexes(items, 10)
        self.assertFalse(s.exact)
        self.assertEqual(s.estimated_benefit, 18)
        self.assertEqual(s.used_bytes, 10)


if __name__ == '__main__':
    unittest.main()
