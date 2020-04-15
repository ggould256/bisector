from core.search_problem import SearchProblem
from core.search_strategy import StrategyRunner

import unittest


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.revisions = ['a', 'b', 'c', 'd']
        self.counter = 0

    def _test_fn(self, revision):
        """Test passed 60% of the time before revision 'c', 40% after."""
        self.counter = (self.counter + 1) % 10
        return self.counter < 6 if revision < 'c' else self.counter < 4


    def test_basic(self):
        problem = SearchProblem(
            versions=self.revisions,
            test_fn=self._test_fn,
            known_setup_cost=10,
            known_test_cost=1)
        guess = StrategyRunner().solve(problem)
        self.assertEqual(guess.best_revision, 'b')
        self.assertGreater(guess.guess_probability, 0.9)


if __name__ == '__main__':
    unittest.main()
