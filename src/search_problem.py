from typing import Callable, Iterable, Generic, TypeVar

VersionType = TypeVar('VersionType')

class SearchProblem(Generic[VersionType]):
    """A SearchProblem describes a bisection problem that we can attempt to
    solve."""

    def __init__(self,
                 versions: Iterable[VersionType],
                 test_fn: Callable[[VersionType], bool],
                 setup_fn: Callable[[VersionType], None]=None,
                 current_version: VersionType=None,
                 known_initial_success_probability: float=None,
                 known_final_success_probability: float=None,
                 known_setup_cost: float=None,
                 known_test_cost: float=None):

        """Create a SearchProblem that will search over @p versions looking for
        changes in the frequency with which @p test_fn passes.

        There are also a large number of optional keyword arguments.

        @p setup_fn, if provided, will be called before @p test_fn is called
        on a new version.  This would be the place to, eg, build a new version
        of the code.

        If @p current_version is set, @p setup_fn will not be called before
        calls to `test_fn(current_version)`.

        @p known_initial_success_probability and @p
        known_final_success_probability allow you to specify that you know the
        frequency of test failures/successes before and after the suspicious
        range.  If either of these is not specified, it will be inferred
        during computation.

        @p known_setup_cost and @p known_test_cost allow you to specify a cost
        function to be used in choosing whether to run an additional test or
        switch to a new version.  If either of these is not specified, it will
        be set to the average runtime of the @p setup_fn or @p test_fn
        respectively, in seconds.
        """
        self.versions = list(versions)
        self.test_fn = test_fn
        self.setup_fn = setup_fn or (lambda _: None)
        self.current_version = current_version
        self.known_initial_success_probability = (
            known_initial_success_probability)
        self.known_final_success_probability = known_final_success_probability
        self.known_setup_cost = known_setup_cost
        self.known_test_cost = known_test_cost
        assert self.test_fn is not None
        assert len(self.versions) > 2
        assert (self.current_version is None) or (
            self.current_version in self.versions)
        assert (self.known_initial_success_probability is None) or (
            0 <= self.known_initial_success_probability <= 1)
        assert (self.known_final_success_probability is None) or (
            0 <= self.known_final_success_probability <= 1)
        assert (self.known_setup_cost is None) or (self.known_setup_cost >= 0)
        assert (self.known_test_cost is None) or (self.known_test_cost > 0)
