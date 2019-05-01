"""Interface for and default implementation of a search strategy.  The default
strategy provided is deliberately ineffecient; it provides a simple baseline
to prove the concept."""

import search_problem

class StrategyRunner:
    """Actually runs a strategy on a search problem.  Its ctor acts as the
    factory for strategy objects."""

    def __init__(self):
        """Create a strategy runner.  Does not now but eventually will take
        factory arguments to instantiate the strategy."""
        self._strategy = DefaultSearchStrategy()

    def solve(problem: search_problem.SearchProblem):
        # XXX TODO(ggould) implement
        pass


class DefaultSearchStrategy
    # XXX TODO(ggould) implement
    pass
