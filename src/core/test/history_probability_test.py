from core.history_probability import Guess, HistoryParameters, history_probabilities, p_value

import random
import unittest


class TestParameterComputation(unittest.TestCase):

    def test_params(self):
        """Test computation of population parameters from history."""
        revisions = ['a', 'b', 'c']
        history = [('a', False), ('a', False), ('b', True), ('b', False), ('c', True), ('c', True), ]
        params = HistoryParameters(revisions, history)
        self.assertEqual(params.success_counts, [0, 1, 2])
        self.assertEqual(params.failure_counts, [2, 1, 0])
        self.assertEqual(params.counts, [2, 2, 2])
        self.assertEqual(params.success_count, 3)
        self.assertEqual(params.failure_count, 3)
        self.assertEqual(params.count, 6)
        self.assertEqual(params.left_sum_successes, [0, 1, 3])
        self.assertEqual(params.left_sum_failures, [2, 3, 3])
        self.assertEqual(params.left_sum_counts, [2, 4, 6])
        self.assertEqual(params.right_sum_successes, [3, 3, 2])
        self.assertEqual(params.right_sum_failures, [3, 1, 0])
        self.assertEqual(params.right_sum_counts, [6, 4, 2])

    def test_p_formula_struture(self):
        """Sanity-check that I have something like the correct formula for p values."""
        revisions = ['a', 'b', 'c']
        history = [('a', False), ('a', False), ('b', True), ('b', False), ('c', True), ('c', True), ]
        params = HistoryParameters(revisions, history)
        assert p_value(params, 0) == p_value(params, 1)  # Scenario is symmetric
        doubled_params = HistoryParameters(revisions, history * 2)
        assert p_value(doubled_params, 0) == p_value(doubled_params, 1)  # Still symmetric...
        assert p_value(params, 0) > p_value(doubled_params, 0)  # ...but increasingly unlikely

    def test_p_formula_behaviour(self):
        """Sanity-check that the p formula works as expected on compliant data."""
        revisions = ['a', 'b', 'c']  # 'b' will be the right answer.
        history = [('a', False), ('b', False), ('c', True), ]
        ps = (1, 1)
        for i in range(5):
            params = HistoryParameters(revisions, history)
            new_ps = (p_value(params, 0), p_value(params, 1))
            assert (new_ps[0] / new_ps[1]) > (ps[0] / ps[1])
            ps = new_ps
            history *= 2

    def test_probabilities(self):
        """Test that revision probability computation works as expected."""
        revisions = ['a', 'b', 'c']
        history = [('a', False), ('a', False), ('b', True), ('b', False), ('c', True), ('c', True), ]
        self.assertEqual(history_probabilities(revisions, history), [0.5, 0.5])
        history += history  # Doubling the number of tests does not break the symmetry
        self.assertEqual(history_probabilities(revisions, history), [0.5, 0.5])
        history.append(('b', True)) # Tip the success probability of 'b' up.
        # 'b' now more closely resembles 'c' than 'a', so ps[0] > ps[1]
        self.assertGreater(history_probabilities(revisions, history)[0], 0.5)
        self.assertLess(history_probabilities(revisions, history)[1], 0.5)
        history += [('b', True)] * 5  # Lots more history should make us more certain.
        self.assertGreater(history_probabilities(revisions, history)[0], 0.9)

    def test_guessing(self):
        """Actually make a guess on difficult random data."""
        random.seed(1)
        revisions = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']  # The right answer will be 'f'.
        history = []
        iterations = 0
        while iterations < 100:
            iterations += 1
            for idx in range(0, 6):
                history += [(revisions[idx], random.random() < 0.4)]
            for idx in range(6, 8):
                history += [(revisions[idx], random.random() < 0.6)]
            guess = Guess(revisions, history)
            if guess.guess_probability > 0.95:
                break
        else:
            self.assertTrue(False)
        assert guess.best_revision == 'f'


if __name__ == '__main__':
    unittest.main()
