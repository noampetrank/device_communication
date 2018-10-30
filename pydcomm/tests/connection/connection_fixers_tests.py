import unittest

import mock
from nose_parameterized import parameterized

from pydcomm.general_android.connection.decorator_helpers import add_adb_recovery_decorator


class AddDecoratorTests(unittest.TestCase):
    def test_add_adb_recovery_decorator__test_connection_fails__fix_happens(self):
        d = {"success": False}

        def decorator(connection):
            d["success"] = True

        adder = add_adb_recovery_decorator(decorator)
        a = mock.Mock()
        a.test_connection.return_value = False
        a = adder(a)
        a.adb(a, "hi")
        self.assertTrue(d["success"])

    @parameterized.expand([
        [True],
        [False]
    ])
    def test_add_adb_recovery_decorator__test_connection_fails__original_adb_is_called(self, connection_success):
        d = {"adb_called": False}
        mock_connection = mock.Mock()

        def adb(*args):
            d["adb_called"] = True

        def decorator(connection):
            pass

        mock_connection.adb.side_effect = adb
        mock_connection.test_connection.return_value = connection_success
        mock_connection = add_adb_recovery_decorator(decorator)(mock_connection)
        mock_connection.adb(mock_connection, "hi")
        self.assertTrue(d["adb_called"])


class TestConnection(object):
    def __init__(self, device_id=None):
        self.connection_good = True
        pass

    def adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
        pass

    def test_connection(self):
        return self.connection_good

