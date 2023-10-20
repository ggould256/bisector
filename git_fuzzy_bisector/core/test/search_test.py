from git_fuzzy_bisector.core.search_problem import SearchProblem
from git_fuzzy_bisector.core.search_strategy import StrategyRunner

import unittest


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.revisions = ['apple', 'banana', 'carrot', 'daikon']
        self.counter = 0

    def _test_fn(self, revision):
        """Test passed 60% of the time before revision 'c', 40% after."""
        self.counter += 1
        success_prob = 0.6 if revision < 'carrot' else 0.4
        return (self.counter * 137 % 100) > (100 * success_prob)

    def test_basic(self):
        problem = SearchProblem(
            versions=self.revisions,
            test_fn=self._test_fn,
            known_setup_cost=10,
            known_test_cost=1)
        guess = StrategyRunner().solve(problem, print_monitor=False)
        self.assertEqual(guess.best_change.before, 'banana')
        self.assertEqual(guess.best_change.after, 'carrot')
        self.assertGreater(guess.guess_probability, 0.9)
        # The basic strategy wastes a lot of work, but should still be able
        # to do its job in a few hundred tests.
        self.assertLess(self.counter, 400)


if __name__ == '__main__':
    unittest.main()
