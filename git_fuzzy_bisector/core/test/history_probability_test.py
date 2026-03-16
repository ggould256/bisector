from git_fuzzy_bisector.core.history_analysis import (
    Change, Guess, HistorySummary, history_probabilities, p_sides_differ)

import random
import unittest


class TestParameterComputation(unittest.TestCase):
    def test_params(self):
        """Test computation of population parameters from history."""
        versions = ['a', 'b', 'c']
        history = [('a', False, 1), ('a', False, 1),
                   ('b', True, 1), ('b', False, 1),
                   ('c', True, 1), ('c', True, 1), ]
        params = HistorySummary(versions, history)
        self.assertEqual(params.versions, ["a", "b", "c"])
        self.assertEqual(params.success_counts, [0, 1, 2])
        self.assertEqual(params.failure_counts, [2, 1, 0])
        self.assertEqual(params.counts, [2, 2, 2])
        self.assertEqual(params.success_count, 3)
        self.assertEqual(params.failure_count, 3)
        self.assertEqual(params.count, 6)
        ab = Change("a", "b")
        bc = Change("b", "c")
        self.assertEqual(params.changes, [ab, bc])
        self.assertEqual(params.left_sum_successes,  {ab: 0, bc: 1})
        self.assertEqual(params.left_sum_failures,   {ab: 2, bc: 3})
        self.assertEqual(params.left_sum_counts,     {ab: 2, bc: 4})
        self.assertEqual(params.right_sum_successes, {ab: 3, bc: 2})
        self.assertEqual(params.right_sum_failures,  {ab: 1, bc: 0})
        self.assertEqual(params.right_sum_counts,    {ab: 4, bc: 2})

    def test_p_formula_struture(self):
        """Sanity-check that I have something like the correct formula for
        p values."""
        versions = ['a', 'b', 'c']
        history = [('a', False, 1), ('a', False, 1),
                   ('b', True, 1), ('b', False, 1),
                   ('c', True, 1), ('c', True, 1), ]
        params = HistorySummary(versions, history)

        # Scenario is symmetric
        self.assertEqual(p_sides_differ(params, Change('a', 'b')),
                         p_sides_differ(params, Change('b', 'c')))

        # Still symmetric with doubled values
        doubled_params = HistorySummary(versions, history * 2)
        self.assertEqual(p_sides_differ(doubled_params, Change('a', 'b')),
                         p_sides_differ(doubled_params, Change('b', 'c')))

        # ...but increasingly unlikely that the null hypo is true at any rev.
        self.assertGreater(p_sides_differ(params, Change('a', 'b')),
                           p_sides_differ(doubled_params, Change('a', 'b')))

    def test_p_formula_behaviour(self):
        """Sanity-check that the p formula works as expected on compliant
        data."""
        versions = ['a', 'b', 'c']  # 'b' will be the right answer.
        history = [('a', False, 1), ('b', False, 1), ('c', True, 1), ]
        ps = (1, 1)
        for i in range(5):
            params = HistorySummary(versions, history)
            new_ps = (p_sides_differ(params, Change('a', 'b')),
                      p_sides_differ(params, Change('b', 'c')))
            assert (new_ps[0] / new_ps[1]) > (ps[0] / ps[1])
            ps = new_ps
            history *= 2

    def test_probabilities(self):
        """Test that version probability computation works as expected."""
        versions = ['a', 'b', 'c']
        history = [('a', False, 1), ('a', False, 1),
                   ('b', True, 1), ('b', False, 1),
                   ('c', True, 1), ('c', True, 1), ]
        ab = Change("a", "b")
        bc = Change("b", "c")
        self.assertEqual(history_probabilities(versions, history),
                         [(ab, 0.5), (bc, 0.5)])
        history += history  # Doubling # of tests does not break the symmetry
        self.assertEqual(history_probabilities(versions, history),
                         [(ab, 0.5), (bc, 0.5)])
        history.append(('b', True, 1)) # Tip the success prob. of 'b' up.
        # 'b' now more closely resembles 'c' than 'a', so ps[0] > ps[1]
        self.assertGreater(history_probabilities(versions, history)[0][1], 0.5)
        self.assertLess(history_probabilities(versions, history)[1][1], 0.5)
        history += [('b', True, 1)] * 5  # Lots more history -> more certain.
        self.assertGreater(history_probabilities(versions, history)[0][1], 0.9)

    def test_guessing(self):
        """Actually make a guess on difficult random data."""
        random.seed(1)
        # The right answer will be 'f'.
        versions = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        history = []
        self.assertEqual(len(history_probabilities(versions, history)),
                         len(versions) - 1)
        for _, prob in history_probabilities(versions, history):
            self.assertEqual(prob, 1 / (len(versions) - 1))

        iterations = 0
        while iterations < 100:
            iterations += 1
            for idx in range(0, 6):
                history += [(versions[idx], random.random() < 0.4, 1)]
            for idx in range(6, 8):
                history += [(versions[idx], random.random() < 0.6, 1)]
            guess = Guess(versions, history)
            if guess.guess_probability > 0.95:
                break
        else:
            self.assertTrue(False, f"Failed to converge after {iterations} iterations")
        self.assertEqual(str(guess.best_change), 'f->g')


if __name__ == '__main__':
    unittest.main()
