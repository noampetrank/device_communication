import unittest
import mock

from pydcomm.infra import Connection


class UnitTestDeviceUtils(unittest.TestCase):

    def setUp(self):
        """
        Executed in the beginning of each test
        """
        self.conn = Connection()

    def tearDown(self):
        """
        Executed in the end of each test
        """
        pass

    # @mock.patch.object(Connection., 'adb')
    def test_ls_ok(self, mock_shell):
        pass
