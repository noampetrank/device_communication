import subprocess32 as subprocess
import unittest
import mock
from nose.tools import assert_raises

from pydcomm.general_android.connection.adb_connection import AdbConnection, AdbConnectionError, get_device_ip, ConnectingError, connect_wireless
from pydcomm.tests.connection.consts import IFCONFIG_BAD, IFCONFIG_GOOD

MODULE_NAME = "pydcomm.general_android.connection.adb_connection"


class WiredAdbConnectionTests(unittest.TestCase):
    def setUp(self):
        self.con = AdbConnection(device_id="avocado")

    @mock.patch(MODULE_NAME + ".subprocess.Popen")
    @mock.patch.object(AdbConnection, "test_connection", lambda x: True)
    def test_adb__valid_input__adb_called_with_input_and_device_id(self, mock_popen):
        stdout = "WONDERFUL STDOUT!!!"
        mock_popen.return_value.communicate.return_value = stdout, mock.Mock()
        mock_popen.return_value.returncode = 0

        command = ["hello", "darkness", "my", "old", "friend"]
        res = self.con.adb(*command)

        mock_popen.assert_has_calls([mock.call(["adb", "-s", "avocado"] + command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)])
        self.assertEqual(res, stdout)

    @mock.patch(MODULE_NAME + ".subprocess.Popen")
    @mock.patch.object(AdbConnection, "test_connection", lambda x: True)
    def test_adb__adb_returns_error_code__raises_appropriate_exception(self, mock_popen):
        stderr = "GREAT ERROR!"
        mock_popen.return_value.communicate.return_value = mock.Mock(), stderr
        mock_popen.return_value.returncode = 4

        with assert_raises(AdbConnectionError) as e:
            self.con.adb("hayush")

        self.assertEqual(e.exception.returncode, 4)
        self.assertEqual(e.exception.stderr, stderr)

    @mock.patch.object(AdbConnection, "test_connection", lambda x: False)
    def test_adb__test_connection_fails__raises_exception(self):
        with assert_raises(AdbConnectionError) as e:
            self.con.adb("hay")
        self.assertIn("test_connection", e.exception.message)

    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_test_connection__valid_connection__return_true(self, mock_check_output):
        mock_check_output.return_value = "hi\n"
        res = self.con.test_connection()
        self.assertTrue(res)

    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_test_connection__time_out__return_false(self, mock_check_output):
        mock_check_output.side_effect = subprocess.TimeoutExpired("echo hi", 1)
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_test_connection__no_device_connected__return_false(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "echo hi")
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_test_connection__no_echo__return_false(self, mock_check_output):
        mock_check_output.return_value = ""
        res = self.con.test_connection()
        self.assertFalse(res)


class GetDeviceIpTests(unittest.TestCase):
    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_get_device_ip__valid_case__get_the_ip(self, mock_check_output):
        ifconfig = IFCONFIG_GOOD
        mock_check_output.side_effect = lambda *args: ifconfig if "ifconfig" in args[0] else ""
        ip = get_device_ip("avocado")
        self.assertEqual(ip, "10.0.0.101")

    @mock.patch(MODULE_NAME + ".subprocess.check_output")
    def test_get_device_ip__device_not_connected_to_wifi__exception(self, mock_check_output):
        ifconfig = IFCONFIG_BAD
        mock_check_output.return_value = ifconfig
        self.assertIsNone(get_device_ip("avocado"))


class WirelessAdbConnectionTests(unittest.TestCase):
    def addPatch(self, name):
        patcher = mock.patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def assert_raises_with_message(self, message):
        with assert_raises(ConnectingError) as e:
            connect_wireless(self.mock_wired_connection, None)
        self.assertIn(message, e.exception.message)

    def setUp(self):
        self.mock_get_device_ip = self.addPatch(MODULE_NAME + ".get_device_ip")
        self.mock_get_device_ip.return_value = "10.0.0.101"
        self.mock_check_call = self.addPatch(MODULE_NAME + ".subprocess.check_call")
        self.mock_raw_input = self.addPatch(MODULE_NAME + ".raw_input")
        self.mock_wired_connection = mock.Mock()
        self.mock_wired_connection.device_id = "penguin"
        self.mock_wired_connection.test_connection.return_value = True

    def test_connect_wirelessly__device_is_not_connected_to_wifi__raise_exception(self):
        self.mock_get_device_ip.return_value = None

        self.assert_raises_with_message("wifi")

    def test_connect__device_is_not_connected_to_computer__raise_exception(self):
        self.mock_wired_connection.test_connection.return_value = False
        self.assert_raises_with_message("connected to PC")

    def raise_exeception_if_correct_command(self, command):
        def side_effect(*args):
            if args[0] == command:
                raise subprocess.CalledProcessError(1, command)
            return None

        return side_effect

    def test_connect__device_got_disconnected_before_adb_tcpip__raise_exception(self):
        self.mock_check_call.side_effect = self.raise_exeception_if_correct_command(["adb", "tcpip", "5555"])
        self.assert_raises_with_message("tcp mode")

    def test_connect__cant_connect_ip__raise_exception(self):
        self.mock_check_call.side_effect = self.raise_exeception_if_correct_command("adb connect 10.0.0.101:5555".split(" "))
        self.assert_raises_with_message("10.0.0.101")
