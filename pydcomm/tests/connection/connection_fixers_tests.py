import unittest

import mock
from nose_parameterized import parameterized

from pydcomm.general_android.connection.decorator_helpers import add_adb_recovery_decorator


class AddDecoratorTests(unittest.TestCase):
    def test_add_adb_recovery_decorator__test_connection_fails__fix_happens(self):
        d = {"success": False}

        def decorator(connection):
            d["success"] = True

        adder = add_adb_recovery_decorator(decorator, "tester")
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
        mock_connection = add_adb_recovery_decorator(decorator, "tester")(mock_connection)
        mock_connection.adb(mock_connection, "hi")
        self.assertTrue(d["adb_called"])


class TestConnection(object):
    def __init__(self, device_id=None):
        self.connection_good = True
        pass

    def adb(self, *params):
        pass

    def test_connection(self):
        return self.connection_good


class NoDeviceConnectedRecoveryTests(unittest.TestCase):
    #     @mock.patch("pydcomm.general_android.connection.connection_fixers.subprocess.check_output")
    #     # https://stackoverflow.com/a/31171719/365408
    #     @mock.patch("pydcomm.general_android.connection.connection_fixers.sys.stdout", new_callable=StringIO)
    #
    #     def test__no_device_disconnected__no_message_shown(self, mock_check_output):
    #         # arrange
    #         mock_connection_cls = TestConnection
    #         mock_connection_cls = add_no_device_connected_recovery(mock_connection_cls)
    #         mock_check_output.return_value = """Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
    # Bus 001 Device 003: ID 8087:0a2b Intel Corp.
    # Bus 001 Device 002: ID 046d:c534 Logitech, Inc. Unifying Receiver
    # Bus 001 Device 004: ID 1bcf:2b96 Sunplus Innovation Technology Inc.
    # Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
    # """
    #
    #         # act
    #         mock_connection = mock_connection_cls()
    #         mock_connection.connection_good = False
    #         mock_connection.adb("hi")
    #
    #         # assert
    # TODO: Get back to this when Dror is here and ask about testing prints and raw_inputs.
    pass


