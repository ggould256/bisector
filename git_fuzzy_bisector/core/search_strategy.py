"""Interface for and default implementation of a search strategy.  The default
strategy provided is deliberately ineffecient; it provides a simple baseline
to prove the concept."""

import math
import time

from git_fuzzy_bisector.core.search_problem import SearchProblem
from git_fuzzy_bisector.core.history_analysis import Guess, HistorySummary

class StrategyRunner:
    """Actually runs a strategy on a search problem.  Its ctor acts as the
    factory for strategy objects."""

    def __init__(self):
        """Create a strategy runner.  Does not now but eventually will take
        factory arguments to instantiate the strategy."""
        self._strategy = DefaultSearchStrategy()

    def solve(self, problem: SearchProblem, print_monitor=False):
        history = []
        guess = Guess(problem.versions, history)
        target_probability = 0.9  # TODO parameterize this (in the problem?)
        setup_cost = problem.known_setup_cost
        test_cost = problem.known_test_cost
        assert (guess.guess_probability <= (1 / (len(problem.versions) - 1)))
        iterations = 0
        while guess.guess_probability < target_probability:
            iterations += 1
            next_revision = self._strategy.next_revision(
                history, problem, setup_cost, test_cost)
            if problem.current_version != next_revision:
                _, setup_cost = self.updated_cost(
                    problem.known_setup_cost, setup_cost, history,
                    lambda: problem.setup_fn(next_revision))
            result, test_cost = self.updated_cost(
                problem.known_test_cost, test_cost, history,
                lambda: problem.test_fn(next_revision))
            history += [(next_revision, result, test_cost)]
            guess = Guess(problem.versions, history)
            if print_monitor:
                print(HistorySummary(problem.versions, history)
                        .fancy_summary())
                print(f"Best guess is change {guess.best_change} "
                      f"with probability {guess.guess_probability:.2f} "
                      f"after {iterations} iterations.")
                print()
        return guess

    @staticmethod
    def updated_cost(known_prior, estimated_prior, history, fn):
        """Evalueate fn(); return its result and the best estimate of its
        cost."""
        # TODO There really are lots of kinds of cost and time is only one.
        start = time.perf_counter()
        result = fn()
        duration = time.perf_counter() - start
        if known_prior:
            return result, known_prior
        if estimated_prior is None:
            return result, duration
        return (result,
            (estimated_prior * len(history) + duration) / (len(history) + 1))


class DefaultSearchStrategy:
    """Extremely basic strategy that blindly tests each revision a few times 
    (setup_cost / test_cost many times) without regard for probabilities.
    Pretty much just meant to establish a baseline for testing."""

    def next_revision(self, history, problem, setup_cost, test_cost):
        if not history:
            return problem.current_version or problem.versions[0]
        cost_ratio = (1 if setup_cost is None or test_cost is None
                      else math.ceil(setup_cost / test_cost))
        revision_counts = [sum(1 for h in history if h[0] == r)
                           for r in problem.versions]
        min_val, min_idx = min((val, idx)
                               for (idx, val) in enumerate(revision_counts))
        max_val = max(revision_counts)
        if problem.current_version is None or max_val - min_val > cost_ratio:
            return problem.versions[min_idx]
        else: return problem.current_version
