from dataclasses import dataclass
from math import floor, sqrt
import scipy.stats
from typing import Callable, Iterable, Generic, List, Tuple, TypeVar

Version = str
TestResult = Tuple[Version, bool, float]  # (version, success/failure, cost of test)
History = List[TestResult]


@dataclass(frozen=True, eq=True)
class Change:
    before: Version
    after: Version

    def to_string(self, max_len=10):
        before = self.before
        after = self.after
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len: return attempt
        trunc_len = floor((max_len - 4) / 2)
        if len(before) > len(after):
            before = before[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len: return attempt
        after = after[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        if len(attempt) <= max_len: return attempt
        before = before[:trunc_len] + "…"
        attempt = f"{before}->{after}"
        return attempt

    def __str__(self):
        return self.to_string()


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
        left_sum_successes  For each change, the number of successes in prior versions
        left_sum_failures   For each change, the number of failures in prior versions
        right_sum_successes For each change, the number of successes in subsequent versions
        right_sum_failures  For each change, the number of failures in subsequent versions
    """

    def __init__(self, versions: List[Version], history: History):
        assert len(versions) > 1
        self.versions = versions
        self.success_counts = [sum(t for (r, t, _) in history if r is rev)
                               for rev in versions]
        self.failure_counts = [sum((not t) for (r, t, _) in history if r is rev)
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
        version_graph_width = len(self.versions)
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
        successes_sparkline = spark(self.success_counts)
        failures_sparkline = spark(self.failure_counts)
        result += right_just_title("Successes: ", first_graph_indent_num) + spark(self.success_counts) + "\n"
        result += right_just_title("Failures: ", first_graph_indent_num) + spark(self.failure_counts) + "\n"

        result += "\n"
        for i, change in enumerate(self.changes):
            new_line = ""
            new_line += f"{first_indent}{'|' * i}{str(change)}"
            additional_indent = ' ' * (second_graph_indent_num - len(new_line))
            new_line += f"{additional_indent}{'|' * i}{str(change)}"
            result += new_line + "\n"
        lss = [self.left_sum_successes[c] for c in self.changes]
        rss = [self.right_sum_successes[c] for c in self.changes]
        lsf = [self.left_sum_failures[c] for c in self.changes]
        rsf = [self.right_sum_failures[c] for c in self.changes]
        lsc = [sum(pair) for pair in zip(lss, lsf)]
        rsc = [sum(pair) for pair in zip(rss, rsf)]
        def two_graph_line(first_title, first_data, second_title, second_data):
            new_line = right_just_title(first_title, first_graph_indent_num)
            new_line += spark(first_data)
            new_line += right_just_title("(after) ", second_graph_indent_num - len(new_line))
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

        ps = [p_value(self, c) for c in self.changes]
        probs = [1/p if p > 0 else None for p in ps]  # unweighted :-(
        result += "\n"
        result += two_graph_line("p-value: ", ps, "probs: ", probs)
        return result


def p_value(history_parameters: HistorySummary,
            change: Change
        ) -> float:
    """Compute the change p-value for a given change.

    Compute a p-value against the hypothesis that the
    versions <= @p change.before and the versions >= change.after
    are from the same distribution.

    @Returns 1 if the history is inadequate to estimate.
    """
    if history_parameters.count == 0:
        return 1.
    hypothesis_p = history_parameters.success_count / history_parameters.count
    left_n = history_parameters.left_sum_counts[change]
    left_successes = history_parameters.left_sum_successes[change]
    right_n = history_parameters.right_sum_counts[change]
    right_successes = history_parameters.right_sum_successes[change]
    if left_n < 1 or right_n < 1:
        return 1.

    p_left = scipy.stats.binomtest(
        left_successes, left_n, hypothesis_p, alternative='two-sided').pvalue
    p_right = scipy.stats.binomtest(
        right_successes, right_n, hypothesis_p, alternative='two-sided').pvalue
    if p_left == 0 or p_right == 0:
        return 0.

    # Fisher's method assumes the p-values are independent, which is not true
    # here (the common expectation value `hypothesis_p` is in common between
    # the two arms).  As such this value is (slightly) unsound for small n.
    _stat, pval = scipy.stats.combine_pvalues(pvalues=[p_left, p_right])
    return pval


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
    ps = [p_value(params, c) for c in changes]

    # The above ps are "p-values" -- P(A==B|r).  For reasons described in
    # other documents, an application of Bayes' theorem tells us that
    # P(r|A!=B) is simply the normalization of the complement of these
    # probabilities.
    weights = [1 / p for p in ps]
    total_weight = sum(weights)
    version_probabilities = [weight / total_weight for weight in weights]

    return [(changes[i], version_probabilities[i]) for i in range(len(changes))]


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
