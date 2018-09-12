import unittest
import mock
from nose_parameterized import parameterized

from pydcomm.general_android.connection.wired_adb_connection import adb_devices

empty_devices = "List of devices attached\n"

no_permissions_single_device = ("1d9b0a84\tno permissions (verify udev rules); see [http://developer.android.com/tools/device.html]\n", ("wired", "1d9b0a84", "no permissions"))
unauthorized = ("4df798d76f98cf6d\tunauthorized\n", ("wired", "4df798d76f98cf6d","no permissions"))

wired_device = ("1d9b0a84\tdevice\n", ("wired", "1d9b0a84", "device"))

wireless_single = ("10.0.0.101:5555\tdevice\n", ("wireless", "10.0.0.101:5555", "device"))


class AdbDevicesTests(unittest.TestCase):
    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess.check_output")
    def test_permutations(self, mock_subprocess):
        temporary = [
            [no_permissions_single_device],
            [no_permissions_single_device, wired_device],
            [wired_device, wireless_single],
            [wireless_single, wireless_single],
            [wired_device, wired_device, wired_device],
            [unauthorized],
            [unauthorized, wireless_single]
        ]
        for devicelist in temporary:
            subprocess_output, expected_output = zip(*devicelist)
            input = empty_devices + "".join(subprocess_output) + "\n\n"
            mock_subprocess.return_value = input
            output = adb_devices()
            self.assertSequenceEqual(output, expected_output)

    @mock.patch("pydcomm.general_android.connection.wired_adb_connection.subprocess")
    def test_empty_device_list(self, mock_subprocess):
        mock_subprocess.check_output.returns(empty_devices)
        output = adb_devices()
        self.assertEqual(output, [])
