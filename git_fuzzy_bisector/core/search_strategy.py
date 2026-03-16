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
        self._strategy = BestChangeSearchStrategy()

    def solve(self,
              problem: SearchProblem,
              print_monitor: bool=False,
              test_limit=None):
        history = []
        guess = Guess(problem.versions, history)
        target_probability = 0.9  # TODO parameterize this (in the problem?)
        setup_cost = problem.known_setup_cost
        test_cost = problem.known_test_cost
        assert (guess.guess_probability <= (1 / (len(problem.versions) - 1)))
        iterations = 0
        while test_limit is None or iterations < test_limit:
            iterations += 1
            next_version = self._strategy.next_version(
                history, problem, setup_cost, test_cost)
            if problem.current_version != next_version:
                _, setup_cost = self.updated_cost(
                    problem.known_setup_cost, setup_cost, history,
                    lambda: problem.setup_fn(next_version))
            problem.current_version = next_version
            result, test_cost = self.updated_cost(
                problem.known_test_cost, test_cost, history,
                lambda: problem.test_fn(next_version))
            history += [(next_version, result, test_cost)]
            guess = Guess(problem.versions, history)
            if print_monitor:
                print(HistorySummary(problem.versions, history)
                        .fancy_summary())
                print(f"Best guess is change {guess.best_change} "
                      f"with probability {guess.guess_probability:.2f} "
                      f"after {iterations} iterations.")
                print()
            if guess.guess_probability > target_probability: break
        else:  # ran out of iterations; break condition not hit.
            print("Test iteration limit hit.")
            exit(1)
        return guess

    @staticmethod
    def updated_cost(known_prior, estimated_prior, history, fn):
        """Evaluate fn(); return its result and the best estimate of its
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
    """Basic strategy that rotates through versions
    
    Extremely basic strategy that blindly tests each revision a few times 
    (setup_cost / test_cost many times) without regard for probabilities.
    Pretty much just meant to establish a baseline for testing."""

    def next_version(self, history, problem, setup_cost, test_cost):
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
        else:
            return problem.current_version


class BestChangeSearchStrategy:
    """Select a revision likely to improve the guess

    Compute the likely change in best-guess-p-value resulting from testing
    each revision; test the best one next.
    """

    def __init__(self, inertia_factor = 0.9):
        """Construct the strategy

        The inertia factor additionally weights testing the current version
        based on the cost of switching versions.  Set to zero there is not
        preference for retesting the current version; set to one the full
        ratio of setup cost to test cost is used."""
        self._inertia = inertia_factor

    def next_version(self, history, problem, setup_cost, test_cost):
        if not history:
            return (problem.current_version or
                    problem.versions[int(len(problem.versions) / 2)])
        versions = problem.versions
        current_version_index = (None if not problem.current_version
                                 else versions.index(problem.current_version))
        summary = HistorySummary(versions, history)
        # Heuristic:  Add one to both success and failure totals to give sane
        # results at low sample sizes.
        success_fraction = (summary.success_count + 1) / (summary.count + 2)
        failure_fraction = 1. - success_fraction
        baseline = Guess(versions, history).guess_probability

        def prob_after_try(version):
            alt_histories = [history + [(version, result, 0)]
                             for result in [True, False]]
            prob_after_success, prob_after_failure = [
                Guess(versions, alt_history).guess_probability
                for alt_history in alt_histories]
            return (prob_after_success * success_fraction +
                    prob_after_failure * failure_fraction)

        rewards = [(baseline - prob_after_try(version)) ** 2
                   for version in versions]
        if problem.current_version:
            status_quo_preference = ((1 + self._inertia)
                                     * (setup_cost + test_cost)
                                     / test_cost)
            print(f"Status quo preference: {status_quo_preference}")
            rewards[current_version_index] *= status_quo_preference
        best_version_index = max(enumerate(rewards), key=lambda x: x[1])[0]
        return versions[best_version_index]
