import subprocess
import unittest
import mock
from nose.tools import assert_raises

from pydcomm.general_android.connection.wired_adb_connection import WiredAdbConnection, AdbConnectionError


class WiredAdbConnectionTests(unittest.TestCase):
    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.Popen")
    def test_adb__valid_input__adb_called_with_input_and_device_id(self, popen_mock):
        stdout = "WONDERFUL STDOUT!!!"
        popen_mock.return_value.communicate.return_value = stdout, mock.Mock()
        popen_mock.return_value.returncode = 0

        con = WiredAdbConnection(device_id="avocado")
        command = ["hello", "darkness", "my", "old", "friend"]
        res = con.adb(*command)

        popen_mock.assert_has_calls([mock.call(["adb", "-s", "avocado"] + command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)])
        self.assertEqual(res, stdout)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.Popen")
    def test_adb__adb_returns_error_code__raises_appropriate_exception(self, popen_mock):
        stderr = "GREAT ERROR!"
        popen_mock.return_value.communicate.return_value = mock.Mock(), stderr
        popen_mock.return_value.returncode = 4

        con = WiredAdbConnection(device_id="avocado")
        with assert_raises(AdbConnectionError) as e:
            con.adb("hayush")


        self.assertEqual(e.exception.returncode, 4)
        self.assertEqual(e.exception.stderr, stderr)
