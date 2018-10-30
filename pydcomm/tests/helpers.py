import mock


class TestCasePatcher(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def addPatch(self, name):
        patcher = mock.patch(name)
        self.test_case.addCleanup(patcher.stop)
        return patcher.start()
