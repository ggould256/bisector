from core.history_probability import Guess, HistoryParameters, history_probabilities

import random
import unittest


class TestParameterComputation(unittest.TestCase):

    def test_params(self):
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

    def test_probabilities(self):
        revisions = ['a', 'b', 'c']
        history = [('a', False), ('a', False), ('b', True), ('b', False), ('c', True), ('c', True), ]
        self.assertEqual(history_probabilities(revisions, history), [0.5, 0.5])
        history += history  # Doubling the number of tests does not break the symmetry
        self.assertEqual(history_probabilities(revisions, history), [0.5, 0.5])
        history.append(('b', True)) # Tip the probability of 'b' up.
        self.assertLess(history_probabilities(revisions, history)[0], 0.5)
        history *= 5  # Lots more history should make us more certain.
        self.assertLess(history_probabilities(revisions, history)[0], 0.01)

    def test_guessing(self):
        random.seed(1)
        revisions = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']  # The right answer will be 'f'.
        history = []
        iterations = 0
        while iterations < 2000:
            iterations += 1
            for idx in range(0, 6):
                history += [(revisions[idx], random.random() < 0.4)]
            for idx in range(6, 8):
                history += [(revisions[idx], random.random() < 0.6)]
            guess = Guess(revisions, history)
            print("with", guess.guess_probability, "it was revision", guess.best_revision, ".")
            if guess.guess_probability > 0.95:
                break
        else:
            self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
