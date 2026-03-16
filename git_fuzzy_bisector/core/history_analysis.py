from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Dict, List, Tuple

import numpy as np
import scipy.stats

Version = str
TestResult = Tuple[Version, bool, float]  # (version, success/failure, cost)
History = List[TestResult]


@dataclass(frozen=True, eq=True)
class Change:
    """Represents a change, i.e. a pair of consecutive versions.

    This class exists solely to prevent fencepost errors (there is one
    fewer changes than versions), but it also makes for a slightly clearer
    pretty-print of the changes in question."""
    before: Version
    after: Version

    def to_string(self, max_len=10):
        before = self.before
        after = self.after
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len:
            return attempt
        trunc_len = floor((max_len - 4) / 2)
        if len(before) > len(after):
            before = before[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len:
            return attempt
        after = after[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len:
            return attempt
        before = before[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        return attempt

    def __str__(self):
        return self.to_string()


# Operations on lists of versions and changes.

def index_map(versions: List[Version]) -> Dict[Version, int]:
    """Returns a map that is the inverse of `versions`."""
    return {v: i for i, v in enumerate(versions)}


def make_changes(versions: List[Version]) -> List[Change]:
    """Returns a list of Change objects for the given list of `versions`."""
    assert len(versions) > 1
    return [Change(before=versions[i-1], after=versions[i])
            for i in range(1, len(versions))]


def make_counts(versions: List[Version], history: History
           ) -> np.ndarray:
    """The counts of successes, failures at each version of a history.

    The return value is an np.array; the shape of the return value is:
        [   [failures at version i],
            [successes at version i]   ]
    """
    result = ([0] * len(history), [0] * len(history))
    index_of = index_map(versions)
    for version, success, _ in history:
        result[1 if success else 0][index_of[version]] += 1
    return np.array(result)


def accumulated_from_left_counts(version_counts: np.ndarray) -> np.ndarray:
    return np.cumsum(version_counts, axis=1)


def accumulated_from_right_counts(version_counts: np.ndarray) -> np.ndarray:
    return np.flip(np.cumsum(np.flip(version_counts, axis=1), axis=1), axis=1)


# The traditional (frequentist / p-value oriented) statistics, used to
# estimate before and after probabilities that will be used in hypothesis
# formation.

def per_change_contingency_tables(versions: List[Version], history: History
                                  ) -> Dict[Change, np.ndarray]:
    """Compute a contingency table for every change in a history.

    The return value is a dict from Change c to a contingency table like:
        [   [Total failures before c,     Total failures after c ],
            [Total successes before c,    Total successes after c]   ]
    """
    changes = make_changes(versions)
    counts = make_counts(versions, history)
    left_counts = accumulated_from_left_counts(counts)
    right_counts = accumulated_from_right_counts(counts)
    result = {}
    for i, change in enumerate(changes):
        contingency_table = np.array(
            [[left_counts[0][i], right_counts[0][i + 1]],
             [left_counts[1][i], right_counts[1][i + 1]]]
        )
        result[change] = contingency_table
    return result


def guess_before_and_after_probabilities(
        versions: List[Version], history: History
        ) -> Tuple[float, float]:
    """Returns success probabilities before and after the change where those
    probabilities are least plausibly the same.  This provides an estimate
    of the true before and after probabilities that should converge to the
    correct values with sufficient samples."""
    index_of = index_map(versions)
    counts = make_counts(versions, history)
    contingency_tables = per_change_contingency_tables(versions, history)
    p_values = {change: scipy.stats.fisher_exact(table)
                for change, table in contingency_tables.items()}
    lowest_p = min(p_values.values())
    candidate_change = [change for change, value in p_values.items()
                        if value == lowest_p][0]
    before_fail, before_success = accumulated_from_left_counts(counts)[
        index_of[candidate_change.before]]
    after_fail, after_success = accumulated_from_right_counts(counts)[
        index_of[candidate_change.after]]
    return (before_success / (before_success + before_fail),
            after_success / (after_success + after_fail))


# The statistics used to find the most likely of the hypotheses.
#
# In brief, given a most likely before-and-after probabilitiy pair, we
# consider one hypothesis for each `Change`, that that change is the boundary
# between the before and after probability regions.  For each hypothesis θ we
# compute the likelihood Lθ = L(θ|x) (probability of observation x under
# hypothesis θ).  We use the likelihood ratio to invert this to L(x|θ), the
# probability of hypothesis θ as opposed to other known hypotheses given
# observation x.

@dataclass(frozen=True, eq=True)
class Hypothesis:
    change: Change
    before_probability: float
    after_probability: float

    @classmethod
    def all_hypotheses(cls,
                       versions: List[Version],
                       history: History
                       ) -> List[Hypothesis]:
        before, after = guess_before_and_after_probabilities(versions, history)
        return [cls(change=c,
                    before_probability=before,
                    after_probability=after)
                for c in make_changes(versions)]

    def likelihood(self, history: History) -> float:
        """Returns Likelihood(Hypothesis | History) (a.k.a. "L(θ|x)")

        That is, returns the probability, assuming hypothesis `θ = self`, of
        the outcome distribution of history
        `x = per_change_contingency_tables(history)`.  (The summarization
        of the history into a contingency table entails an assumption that
        the underlying experiments are i.i.d.)
        """
        ...


class HistorySummary:
    """Holds a variety of useful accumulated statistics about a history:
        versions            Name of each version
        success_counts      For each version, number of successes at version
        failure_counts      For each version, number of failures at version
        counts              For each version, number of tests at version
        success_count       Total number of successful tests over all versions
        failure_count       Total number of failed tests over all versions
        count               Total number of tests over all versions
        changes             Every version-to-version change
        left_sum_successes  For each change, # of successes in prior versions
        left_sum_failures   For each change, # of failures in prior versions
        right_sum_successes For each change, # of successes in subsequent vers
        right_sum_failures  For each change, # of failures in subsequent vers
    """

    def __init__(self, versions: List[Version], history: History):
        assert len(versions) > 1
        self.versions = versions
        self.success_counts = [sum(t for (r, t, _) in history if r is rev)
                               for rev in versions]
        self.failure_counts = [sum((not t)
                                   for (r, t, _) in history if r is rev)
                               for rev in versions]
        self.counts = [len([r for (r, _, _) in history if r is rev])
                       for rev in versions]

        self.success_count = sum(self.success_counts)
        self.failure_count = sum(self.failure_counts)
        self.count = sum(self.counts)

        self.changes = [Change(versions[i], versions[i+1])
                        for i in range(len(versions) - 1)]
        self.left_sum_successes = {}
        accumulator = 0
        for i, c in enumerate(self.changes):
            accumulator += self.success_counts[i]
            self.left_sum_successes[c] = accumulator

        self.left_sum_failures = {}
        accumulator = 0
        for i, c in enumerate(self.changes):
            accumulator += self.failure_counts[i]
            self.left_sum_failures[c] = accumulator

        self.left_sum_counts = {
            c: self.left_sum_failures[c] + self.left_sum_successes[c]
            for c in self.changes}

        self.right_sum_successes = {
            c: self.success_count - self.left_sum_successes[c]
            for c in self.changes}
        self.right_sum_failures = {
            c: self.failure_count - self.left_sum_failures[c]
            for c in self.changes}
        self.right_sum_counts = {
            c: self.count - self.left_sum_counts[c]
            for c in self.changes}

    def __str__(self):
        s = "{\n"
        for (k, v) in self.__dict__.items():
            s += str(k) + ": " + str(v) + "\n"
        s += "}"
        return s

    def fancy_summary(self):
        """Returns a fancy sparkline unicode-art view of the history."""
        import sparklines
        def spark(vals):
            return "".join(sparklines.sparklines(
                vals, minimum=0, maximum=(None if any(vals) else 1)))

        # Indentation picture:
        #               VERSIONNAME
        #               |||||||VERSIONNAME
        #         TITLE ========
        # [first ident ][graph ][hangover]
        #               CHANGENAME          CHANGENAME
        #               |||||||CHANGENAME   |||||||CHANGENAME
        #         TITLE ========      TITLE ========
        # [first ident ][graph ][hangover]
        # [second indent...................][graph ]
        LONGEST_FIRST_TITLE = 20  # "Succ. rate (before)"
        LONGEST_SECOND_TITLE = 8  # "(after) "
        first_graph_indent_num = LONGEST_FIRST_TITLE
        _version_graph_width = len(self.versions)
        change_graph_width = len(self.changes)
        change_graph_hangover = max(len(str(c)) for c in self.changes)
        second_graph_indent_num = (
            first_graph_indent_num
            + change_graph_width
            + max(LONGEST_SECOND_TITLE + 1, change_graph_hangover))

        def right_just_title(title, width):
            return ' ' * (width - len(title)) + title

        result = ""
        first_indent = ' ' * first_graph_indent_num
        for i, rev in enumerate(self.versions):
            new_line = ""
            new_line += f"{first_indent}{'|' * i}{str(rev)}"
            result += new_line + "\n"
        _successes_sparkline = spark(self.success_counts)
        _failures_sparkline = spark(self.failure_counts)
        result += right_just_title("Successes: ", first_graph_indent_num)
        result += spark(self.success_counts) + "\n"
        result += right_just_title("Failures: ", first_graph_indent_num)
        result += spark(self.failure_counts) + "\n"

        result += "\n"
        for i, change in enumerate(self.changes):
            new_line = ""
            new_line += f"{first_indent}{'|' * i}{str(change)}"
            additional_indent = (
                ' ' * (second_graph_indent_num - len(new_line)))
            new_line += f"{additional_indent}{'|' * i}{str(change)}"
            result += new_line + "\n"
        lss = [self.left_sum_successes[c] for c in self.changes]
        rss = [self.right_sum_successes[c] for c in self.changes]
        lsf = [self.left_sum_failures[c] for c in self.changes]
        rsf = [self.right_sum_failures[c] for c in self.changes]
        lsc = [sum(pair) for pair in zip(lss, lsf)]
        rsc = [sum(pair) for pair in zip(rss, rsf)]
        def two_graph_line(first_title, first_data,
                           second_title, second_data):
            new_line = right_just_title(first_title, first_graph_indent_num)
            new_line += spark(first_data)
            new_line += right_just_title(
                second_title, second_graph_indent_num - len(new_line))
            new_line += spark(second_data) + "\n"
            return new_line
        result += two_graph_line("Successes (before) ", lss, "(after) ", rss)
        result += two_graph_line("Failures (before) ", lsf, "(after) ", rsf)

        lratio = []
        rratio = []
        for i, _ in enumerate(self.changes):
            if lsc[i] == 0:
                lratio.append(None)
            else:
                lratio.append(lss[i] / lsc[i])
            if rsc[i] == 0:
                rratio.append(None)
            else:
                rratio.append(rss[i] / rsc[i])
        result += two_graph_line("Succ. rate (before) ", lratio,
                                 "(after) ", rratio)

        ps = [p_sides_differ(self, c) for c in self.changes]
        probs = [1/p if p > 0 else None for p in ps]  # unweighted :-(
        result += "\n"
        result += two_graph_line("p-value: ", ps, "probs: ", probs)
        return result


def p_sides_differ(
        history_params: HistorySummary,
        change: Change
    ) -> float:
    """Compute the p value that the sides of a change differ.

    Compute a p-value against the hypothesis that the
    versions <= @p change.before and the versions >= change.after
    are from the same distribution.

    NOTE:  In context, this is not a P-value as such:  The null hypothesis
    is in fact always false _ex hypothesi_ within the definition of the
    problem.  This must be corrected for via re-weighting later to ensure
    that the complements of the P values sum to 1 (i.e. that there is exactly
    one guilty revision) or, alternatively, that the P values sum to
    num_changes - 1 (i.e. that there are N-1 revisions without a change).

    @Returns 1 if the history is inadequate to estimate.
    """
    outcome_matrix = np.array(
        [[history_params.left_sum_successes[change],
          history_params.right_sum_successes[change]],
         [history_params.left_sum_failures[change],
          history_params.right_sum_failures[change]]])
    result = scipy.stats.fisher_exact(outcome_matrix)
    return result.pvalue  # type: ignore -- scipy type hints are incomplete.

def history_probabilities(
        versions: List[Version],
        history: History
    ) -> List[Tuple[Change, float]]:
    """Given a list of versions and tests against those versions, compute
    the likelihood that each version is the last one before a change in
    success probability.  The last version has no well-defined probability
    and is omitted.
    """
    params = HistorySummary(versions, history)
    changes = params.changes
    ps = [p_sides_differ(params, c) for c in changes]
    if [p == 1.0 for p in ps]:
        # If all p values are 1, then we have no information to distinguish
        # the versions; return a uniform distribution.
        return [(c, 1 / len(changes)) for c in changes]

    # The above ps are "p-values" -- P(A==B|r).  For reasons described in
    # other documents, an application of Bayes' theorem tells us that
    # P(r|A!=B) is the normalization of the complement of these probabilities.
    total_p_complements = sum((1 - p for p in ps))
    version_probabilities = [1 - (p / total_p_complements) for p in ps]

    return [(changes[i], version_probabilities[i])
            for i in range(len(changes))]


class Guess:
    """A structure representing a best-guess estimate of the critical
    change and its likelihood.
    """
    def __init__(self, versions: List[Version], history: History):
        self.history = history
        probabilities = history_probabilities(versions, history)
        (self._best_version_index,
         (self._best_change, self._guess_probability)) = max(
             enumerate(probabilities), key=lambda x: x[1][1])

    @property
    def best_change(self):
        return self._best_change

    @property
    def guess_probability(self):
        return self._guess_probability
