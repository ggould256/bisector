"""Defines structures and interfaces used by the core algorithm."""

from typing import Optional

import attr
import scipy.stats


Revision = str

def is_probability(_instance, attribute, value):
    if not (0 <= value <= 1):
        raise ValueError("probability `%s` (value %s) is not in 0-1"
                        % (attribute, value))


@attr.s(frozen=True)
class ProblemSpecification:
    """Things known about a problem prior to any test results."""
    revisions: List[Revision] = attr.ib()
    starting_revision: Optional[Revision] = attr.ib(default=None)
    test_cost: Optional[float] = attr.ib(default=None)
    revisions_change_cost: Optional[float] = attr.ib(default=None)
    known_probability_before: Optional[float] = attr.ib(
        default=None, validator=is_probability)
    known_probability_after: Optional[float] = attr.ib(
        default=None, validator=is_probability)


@attr.s(frozen=True)
class TestRecord:
    """Record of a single test."""
    revison: Revision = attr.ib()
    outcome: bool = attr.ib()
    cost: float = attr.ib()


@attr.s
class ProblemState:
    """All the relevant information about a problem currently being worked,
    (the original specification, the test history, and the current
    revision) as well as various simple utility functions on them.

    :param: specification is the problem description
    :param: history a list of `TestRecord` if any tests have been performed.
    """

    # The algorithm to convert a history into a map revision->probability
    # is this:
    #
    # For each revision, collect the total number of successes and failures
    # before and after that revision.  Then for that revision use a Z-test
    # (binomial test against the null hypothesis that the probabilities
    # before and after are the same).  Convert the resulting Zs to ps.
    #
    # The p value is P(A!=B|r) where A is the probability before the change,
    # B the probability after the change, and r is a candidate revision for
    # the change.
    #
    # By Bayes, P(r|A!=B) = P(A!=B|r) * P(r) / P(A!=B).  A!=B is 1 (ex
    # hypothesi) and our prior for P(r) is uniform over the nr revisions.  So
    # P(r) = P(A!=B|r) / rn.  So as long as we normalize the z-derived
    # probabilities, they give us the revision probabilities.
    #
    # Normalizing will also efface the distinction between one-tailed and
    # two-tailed probability, so I will ignore tailedness.

    specification: ProblemSpecification = attr.ib()
    history: List[TestRecord] = attr.ib(factory=list)
    current_revision: Optional[Revision] = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.current_revision = (
            self.history[-1].revision if self.history else
            self.specification.starting_revision)  # Could still be None!

    def best_guess_revision(self):
        """@return (revision, probability) for the revision that is currently
        considered most likely to be the first one at a new success
        probability."""
        revision, probability = max(self.revision_probabilities(),
                                    key=lambda x: x[1])
        return revision, probability

    def revision_probabilities(self):
        """@return [(revision, probability), ...] for every revision.
        `probability` is the probability that that revision is the first of a
        different probability.  Thus, `probability`s will sum to 1."""
        zs = self.revision_zs()
        ps = [(revision, scipy.stats.norm.cdf(z)) for (revision, z) in zs]
        return ps

    def revision_zs(self):
        zs = []
        for revision in self._specification.revisions():

