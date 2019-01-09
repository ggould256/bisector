from math import sqrt
import scipy.stats
from typing import Callable, Iterable, Generic, List, Tuple, TypeVar

Revision = str
TestResult = Tuple[Revision, bool]

class HistoryParameters:
    """Holds a variety of useful accumulated statistics about a history:
        success_counts      For each revision, number of successes at revision
        failure_counts      For each revision, number of failures at revision
        counts              For each revision, number of tests at revision
        success_count       Total number of successful tests over all revisions
        failure_count       Total number of failed tests over all revisions
        count               Total number of tests over all revisions
        left_sum_successes  For each revision, the number of successes at that or any prior revision
        left_sum_failures   For each revision, the number of failures at that or any prior revision
        right_sum_successes For each revision, the number of successes at that or any subsequent revision
        right_sum_failures  For each revision, the number of failures at that or any subsequent revision
    """

    def __init__(self, revisions: List[Revision], history: List[TestResult]):
        self.success_counts = [sum(t for (r, t) in history if r is rev) for rev in revisions]
        self.failure_counts = [sum((not t) for (r, t) in history if r is rev) for rev in revisions]
        self.counts = [len([r for (r, _) in history if r is rev]) for rev in revisions]

        self.success_count = sum(self.success_counts)
        self.failure_count = sum(self.failure_counts)
        self.count = sum(self.counts)

        self.left_sum_successes = []
        accumulator = 0
        for s in self.success_counts:
            accumulator += s
            self.left_sum_successes.append(accumulator)

        self.left_sum_failures = []
        accumulator = 0
        for f in self.failure_counts:
            accumulator += f
            self.left_sum_failures.append(accumulator)

        self.left_sum_counts = []
        accumulator = 0
        for c in self.counts:
            accumulator += c
            self.left_sum_counts.append(accumulator)

        self.right_sum_successes = [self.success_count - lss for lss in [0] + self.left_sum_successes][:-1]
        self.right_sum_failures = [self.failure_count - lsf for lsf in [0] + self.left_sum_failures][:-1]
        self.right_sum_counts = [self.count - lsc for lsc in [0] + self.left_sum_counts][:-1]

    def __str__(self):
        s = "{\n"
        for (k, v) in self.__dict__.items():
            s += str(k) + ": " + str(v) + "\n"
        s += "}"
        return s


def p_value(history_parameters: HistoryParameters, revision_index: int):
    """Compute a p-value against the hypothesis that the revisions <= @p revision_index and the revisions >= revision_index are from the same distribution."""
    hypothesis_p = history_parameters.success_count / history_parameters.count
    left_n = history_parameters.left_sum_counts[revision_index]
    left_successes = history_parameters.left_sum_successes[revision_index]
    right_n = history_parameters.right_sum_counts[revision_index + 1]
    right_successes = history_parameters.right_sum_successes[revision_index + 1]

    p_left = scipy.stats.binom_test(left_successes, left_n, hypothesis_p, alternative='two-sided')
    p_right = scipy.stats.binom_test(right_successes, right_n, hypothesis_p, alternative='two-sided')
    p = 1 / (1 / p_left + 1 / p_right)  # Combine p-values via harmonic sum; TODO(ggould) is this correct?
    return p


def history_probabilities(revisions: List[Revision], history: List[TestResult]) -> List[float]:
    """Given a list of revisions and tests against those revisions, compute the likelihood that each revision is the last one before a change in success probability.
    The last revision has no well-defined probability and is omitted."""
    params = HistoryParameters(revisions, history)
    ps = [p_value(params, i) for i in range(0, len(revisions) - 1)]
    total_ps = sum(ps)

    p_complements = [1 - p for p in ps]
    total_p_complement = sum(p_complements)
    # The above ps are "p-values" -- P(A==B|r).  For reasons described in other documents, an application of Bayes' theorem tells us that P(r|A!=B)
    # is simply the normalization of the complement of these probabilities.
    #revision_probabilities = [pc / total_p_complement for pc in p_complements]
    revision_probabilities = [p_complement / total_p_complement for p_complement in p_complements]
    return revision_probabilities


class Guess:
    """A structure representing a best-guess estimate of the critical revision and its likelihood."""
    def __init__(self, revisions: List[Revision], history: List[TestResult]):
        probabilities = history_probabilities(revisions, history)
        print(probabilities)
        (self.best_revision_index, self.guess_probability) = max(enumerate(probabilities), key=lambda x: x[1])
        self.best_revision = revisions[self.best_revision_index]
