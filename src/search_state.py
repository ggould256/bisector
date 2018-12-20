import search_problem
import attr

VersionType = TypeVar('VersionType')

@attr.s
class TestRecord:
    version = attr.ib()
    outcome = attr.ib()
    setup_time = attr.ib()
    test_time = attr.ib()


class TestHistory:
    version = attr.ib()
    tests = attr.ib(factory=list)


class SearchState(Generic[VersionType]):
    def __init__(self,
                 problem: search_problem.SearchProblem):
        self._problem = problem
        self._histories = [TestHistory(version=version)
                           for version in problem.versions]
