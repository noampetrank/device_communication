import unittest
import mock
from nose.tools import assert_raises

from pydcomm.general_android.connection.device_selector import adb_devices, add_choose_first_behavior, add_user_choice_behavior

empty_devices = "List of devices attached\n"

no_permissions_single_device = ("1d9b0a84\tno permissions (verify udev rules); see [http://developer.android.com/tools/device.html]\n", ("wired", "1d9b0a84", "no permissions"))
unauthorized = ("4df798d76f98cf6d\tunauthorized\n", ("wired", "4df798d76f98cf6d", "no permissions"))

wired_device = ("1d9b0a84\tdevice\n", ("wired", "1d9b0a84", "device"))

wireless_single = ("10.0.0.101:5555\tdevice\n", ("wireless", "10.0.0.101:5555", "device"))


class AdbDevicesTests(unittest.TestCase):
    @staticmethod
    def get_mock_connection_with_adb_output(output):
        conn = mock.Mock()
        conn.adb.return_value = output
        return conn

    def test_permutations(self):
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
            output = adb_devices(self.get_mock_connection_with_adb_output(input))
            self.assertSequenceEqual(output, expected_output)

    def test_empty_device_list(self):
        output = adb_devices(self.get_mock_connection_with_adb_output(empty_devices))
        self.assertEqual(output, [])


class ChooseFirstDeviceDecoratorTests(unittest.TestCase):
    def setUp(self):
        self.a = mock.Mock()
        self.a = add_choose_first_behavior(self.a)

    @mock.patch("pydcomm.general_android.connection.device_selector.adb_devices")
    def test_choose_first__empty_devices__raise_exception(self, adb_devices_mock):
        adb_devices_mock.return_value = []
        assert_raises(EnvironmentError, self.a._get_device_to_connect, self.a)

    @mock.patch("pydcomm.general_android.connection.device_selector.adb_devices")
    def test_choose_first__one_device__returns_the_device(self, adb_devices_mock):
        adb_devices_mock.return_value = [("wired", "devicename", "device")]
        self.assertEqual(self.a._get_device_to_connect(self.a), "devicename")

    @mock.patch("pydcomm.general_android.connection.device_selector.adb_devices")
    def test_choose_first__two_devices__returns_first_device(self, adb_devices_mock):
        adb_devices_mock.return_value = [("wired", "devicename", "device"),
                                         ("wireless", "not the device", "device")]
        self.assertEqual(self.a._get_device_to_connect(self.a), "devicename")


class UserChoiceDeviceDecoratorTests(unittest.TestCase):
    def setUp(self):
        self.a = mock.Mock()
        self.a = add_user_choice_behavior(self.a)

    @mock.patch("pydcomm.general_android.connection.device_selector.adb_devices")
    @mock.patch("pydcomm.general_android.connection.device_selector.UserInput")
    def test_user_choice__no_devices_connected__adb_devices_called_multiple_times(self, user_input_mock, adb_devices_mock):
        adb_devices_mock.side_effect = [
            [],
            [("wired", "devicenome", "device")]
        ]
        self.a._get_device_to_connect(self.a)
        self.assertEqual(adb_devices_mock.call_count, 2)

    @mock.patch("pydcomm.general_android.connection.device_selector.adb_devices")
    @mock.patch("pydcomm.general_android.connection.device_selector.UserInput")
    def test_user_choice__single_devices_connected__correct_menu_is_shown_and_value_is_returned(self, user_input_mock, adb_devices_mock):
        adb_devices_mock.return_value = [("wired", "devicenome", "device")]
        user_input_mock.menu.return_value = 3
        res = self.a._get_device_to_connect(self.a)
        user_input_mock.menu.assert_has_calls([mock.call([("devicenome", "device")])])
        self.assertEqual(res, 3)
