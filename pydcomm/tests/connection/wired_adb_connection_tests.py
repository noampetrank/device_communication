import subprocess32 as subprocess
import unittest
import mock
from nose.tools import assert_raises

from pydcomm.general_android.connection.wired_adb_connection import WiredAdbConnection, AdbConnectionError


class WiredAdbConnectionTests(unittest.TestCase):
    def setUp(self):
        self.con = WiredAdbConnection(device_id="avocado")

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.Popen")
    def test_adb__valid_input__adb_called_with_input_and_device_id(self, mock_popen):
        stdout = "WONDERFUL STDOUT!!!"
        mock_popen.return_value.communicate.return_value = stdout, mock.Mock()
        mock_popen.return_value.returncode = 0

        command = ["hello", "darkness", "my", "old", "friend"]
        res = self.con.adb(*command)

        mock_popen.assert_has_calls([mock.call(["adb", "-s", "avocado"] + command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)])
        self.assertEqual(res, stdout)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.Popen")
    def test_adb__adb_returns_error_code__raises_appropriate_exception(self, mock_popen):
        stderr = "GREAT ERROR!"
        mock_popen.return_value.communicate.return_value = mock.Mock(), stderr
        mock_popen.return_value.returncode = 4

        with assert_raises(AdbConnectionError) as e:
            self.con.adb("hayush")

        self.assertEqual(e.exception.returncode, 4)
        self.assertEqual(e.exception.stderr, stderr)

    @mock.patch.object(WiredAdbConnection, "test_connection", lambda x: False)
    def test_adb__test_connection_fails__raises_exception(self):
        with assert_raises(AdbConnectionError) as e:
            self.con.adb("hay")
        self.assertIn("test_connection", e.exception.message)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.check_output")
    def test_test_connection__valid_connection__return_true(self, mock_check_output):
        mock_check_output.return_value = "hi\n"
        res = self.con.test_connection()
        self.assertTrue(res)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.check_output")
    def test_test_connection__time_out__return_false(self, mock_check_output):
        mock_check_output.side_effect = subprocess.TimeoutExpired("echo hi", 1)
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.check_output")
    def test_test_connection__no_device_connected__return_false(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "echo hi")
        res = self.con.test_connection()
        self.assertFalse(res)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.check_output")
    def test_test_connection__no_echo__return_false(self, mock_check_output):
        mock_check_output.return_value = ""
        res = self.con.test_connection()
        self.assertFalse(res)
