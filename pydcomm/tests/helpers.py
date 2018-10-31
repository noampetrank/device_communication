import StringIO
import sys

import mock


class TestCasePatcher(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def addPatch(self, name):
        patcher = mock.patch(name)
        self.test_case.addCleanup(patcher.stop)
        return patcher.start()

    def addObjectPatch(self, object, name):
        patcher = mock.patch.object(object, name)
        self.test_case.addCleanup(patcher.stop)
        return patcher.start()


class MockStdout():
    def __init__(self):
        pass

    def __enter__(self):
        self.captured_output = StringIO.StringIO()
        sys.stdout = self.captured_output
        return self.captured_output

    def __exit__(self, *args):
        sys.stdout = sys.__stdout__
