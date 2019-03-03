import StringIO
import sys
import unittest
from nose.tools import assert_raises

import mock
import subprocess32 as subprocess
from pydcomm.general_android.connection.internal_adb_connection import InternalAdbConnection
from pydcomm.general_android.connection.wireless_adb_connection import get_device_ip, connect_wireless
from pydcomm.public.iconnection import ConnectionClosedError, CommandFailedError, ConnectingError
from pydcomm.tests.connection.consts import IFCONFIG_BAD, IFCONFIG_GOOD
from pydcomm.tests.helpers import TestCasePatcher

WIRED_MODULE_NAME = "pydcomm.general_android.connection.internal_adb_connection"


class WiredAdbConnectionTests(unittest.TestCase):
    def setUp(self):
        self.con = None # To prevent some warnings

        @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
        def create_connection(mock_popen):
            mock_popen.return_value.communicate.return_value = "hi", mock.Mock()
            mock_popen.return_value.returncode = 0
            self.con = InternalAdbConnection(device_id="avocado")

        create_connection()

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    @mock.patch.object(InternalAdbConnection, "test_connection", lambda x: True)
    def test_adb__valid_input__adb_called_with_input_and_device_id(self, mock_popen):
        stdout = "WONDERFUL STDOUT!!!"
        mock_popen.return_value.communicate.return_value = stdout, mock.Mock()
        mock_popen.return_value.returncode = 0

        command = "hello darkness my old friend"
        res = self.con.adb(command)

        mock_popen.assert_has_calls(
            [mock.call(["adb", "-s", "avocado"] + command.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)])
        self.assertEqual(res, stdout)

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    @mock.patch.object(InternalAdbConnection, "test_connection", lambda x: True)
    def test_adb__adb_returns_error_code__raises_appropriate_exception(self, mock_popen):
        stderr = "GREAT ERROR!"
        mock_popen.return_value.communicate.return_value = mock.Mock(), stderr
        mock_popen.return_value.returncode = 4

        with assert_raises(CommandFailedError) as e:
            self.con.adb("hayush")

        self.assertEqual(e.exception.returncode, 4)
        self.assertEqual(e.exception.stderr, stderr)

    @mock.patch.object(InternalAdbConnection, "test_connection", lambda x: False)
    def test_adb__test_connection_fails__raises_exception(self):
        with assert_raises(ConnectionClosedError) as e:
            self.con.adb("hay")

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    def test_test_connection__valid_connection__return_true(self, mock_popen):
        mock_popen.return_value.communicate.return_value = "hi", mock.Mock()
        mock_popen.return_value.returncode = 0
        res = self.con.test_connection()
        self.assertTrue(res)

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    def test_test_connection__time_out__return_false(self, mock_popen):
        mock_popen.side_effect = subprocess.TimeoutExpired("echo hi", 1)
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    def test_test_connection__no_device_connected__return_false(self, mock_popen):
        mock_popen.return_value.communicate.return_value = "hi", mock.Mock()
        mock_popen.return_value.returncode = 1
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch(WIRED_MODULE_NAME + ".subprocess.Popen")
    def test_test_connection__no_echo__return_false(self, mock_popen):
        mock_popen.return_value.communicate.return_value = "", mock.Mock()
        mock_popen.return_value.returncode = 0
        res = self.con.test_connection()
        self.assertFalse(res)

    def test_disconnect__disconnect__cant_run_adb(self):
        self.con.disconnect()
        with self.assertRaises(ConnectionClosedError):
            self.con.adb("shell echo hi")


class GetDeviceIpTests(unittest.TestCase):
    def test_get_device_ip__valid_case__get_the_ip(self):
        ifconfig = IFCONFIG_GOOD
        mock_connection = mock.Mock()
        mock_connection.adb.side_effect = lambda *args, **kwargs: ifconfig if "ifconfig" in args[0] else ""
        ip = get_device_ip(mock_connection)
        self.assertEqual(ip, "10.0.0.101")

    def test_get_device_ip__device_not_connected_to_wifi__exception(self):
        ifconfig = IFCONFIG_BAD
        mock_connection = mock.Mock()
        mock_connection.adb.return_value = ifconfig
        self.assertIsNone(get_device_ip(mock_connection))


WIRELESS_MODULE_NAME = "pydcomm.general_android.connection.wireless_adb_connection"


class WirelessAdbConnectionTests(unittest.TestCase):
    def assert_raises_with_message(self, message):
        with assert_raises(ConnectingError) as e:
            connect_wireless(self.mock_wired_connection, None)
        self.assertIn(message, e.exception.message)

    def setUp(self):
        self.patcher = TestCasePatcher(self)
        self.mock_get_device_ip = self.patcher.addPatch(WIRELESS_MODULE_NAME + ".get_device_ip")
        self.mock_get_device_ip.return_value = u"10.0.0.101"
        self.mock_raw_input = self.patcher.addPatch(WIRELESS_MODULE_NAME + ".raw_input")
        self.mock_wired_connection = mock.Mock()
        self.mock_wired_connection.device_id = "penguin"
        self.mock_wired_connection.test_connection.return_value = True

    @mock.patch(WIRELESS_MODULE_NAME + ".UserInput.yes_no")
    def test_connect_wirelessly__device_is_not_connected_to_wifi__raise_exception(self, moch_yes_no):
        self.mock_get_device_ip.return_value = None
        moch_yes_no.return_value = False    # ADB connection failed. Do you want to try again? n

        self.assert_raises_with_message("wifi")

    def test_connect__device_is_not_connected_to_computer__raise_exception(self):
        self.mock_wired_connection.test_connection.return_value = False
        self.assert_raises_with_message("connected to PC")

    @staticmethod
    def raise_connection_error_if_command_equals(command):
        def side_effect(*args, **kwargs):
            if args[0] == command:
                raise CommandFailedError(command)

            return None

        return side_effect

    @staticmethod
    def return_value_if_command_equals(command, value):
        def side_effect(*args, **kwargs):
            if args[0] == command:
                return value

            return None

        return side_effect

    def test_connect__device_got_disconnected_before_adb_tcpip__raise_exception(self):
        self.mock_wired_connection.adb.side_effect = self.raise_connection_error_if_command_equals("tcpip 5555")
        self.assert_raises_with_message("tcp mode")

    @mock.patch(WIRELESS_MODULE_NAME + ".UserInput.yes_no")
    def test_connect__cant_connect_ip__raise_exception(self, moch_yes_no):
        self.mock_wired_connection.adb.side_effect = self.raise_connection_error_if_command_equals(
            "connect 10.0.0.101:5555")
        moch_yes_no.return_value = False    # ADB connection failed. Do you want to try again? n

        self.assert_raises_with_message("10.0.0.101")

    @mock.patch(WIRELESS_MODULE_NAME + ".get_connected_interfaces_and_addresses")
    def test_connect__device_is_not_on_same_network__user_is_asked_to_change_network(self, mock_get_interfaces):
        mock_get_interfaces.return_value = [(u'enx000acd2b99a2',
                                             [{'addr': u'10.0.0.107',
                                               'broadcast': u'10.0.0.255',
                                               'netmask': u'255.255.255.0'}]),
                                            (u'docker0',
                                             [{'addr': u'172.17.0.1',
                                               'broadcast': u'172.17.255.255',
                                               'netmask': u'255.255.0.0'}])]
        self.mock_get_device_ip.side_effect = [u"192.168.1.1", u"10.0.0.104"]
        self.mock_wired_connection.adb.side_effect = self.return_value_if_command_equals("connect 10.0.0.104:5555",
                                                                                         "connected to 10.0.0.104:5555")

        captured_output = StringIO.StringIO()
        sys.stdout = captured_output

        connect_wireless(self.mock_wired_connection, None)

        sys.stdout = sys.__stdout__
        self.assertIn("Device is not connected to the same network as the computer, please change and press enter",
                      captured_output.getvalue())
