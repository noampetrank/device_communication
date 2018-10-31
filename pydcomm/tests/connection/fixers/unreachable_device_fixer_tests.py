import unittest

import mock
from pydcomm.general_android.connection.fixers.unreachable_device_fixer import unreachable_device_fix
from pydcomm.tests.helpers import MockStdout

TESTED_MODULE_NAME = "pydcomm.general_android.connection.fixers.unreachable_device_fixer"


class UnreachableDeviceFixerTests(unittest.TestCase):
    def setUp(self):
        self.connection = mock.Mock()
        self.connection.device_id = u"10.0.0.104:5555"

    @mock.patch(TESTED_MODULE_NAME + ".connect_to_wireless_adb")
    @mock.patch(TESTED_MODULE_NAME + ".subprocess.call")
    @mock.patch(TESTED_MODULE_NAME + ".query_yes_no")
    def test_unreachable_device_fix__device_connected__user_is_not_prompted_no_reconnect(self, mock_query_yes_no,
                                                                                         mock_call,
                                                                                         mock_connect_to_wireless_adb):
        mock_call.return_value = 0

        with MockStdout() as mock_stdout:
            unreachable_device_fix(self.connection)
            self._verify_message_not_printed_to_user(mock_stdout.getvalue())
            mock_query_yes_no.assert_not_called()
            mock_connect_to_wireless_adb.assert_not_called()

    @mock.patch(TESTED_MODULE_NAME + ".connect_to_wireless_adb")
    @mock.patch(TESTED_MODULE_NAME + ".subprocess.call")
    @mock.patch(TESTED_MODULE_NAME + ".query_yes_no")
    def test_unreachable_device_fix__happy_path__user_is_prompted_and_reconnect(self, mock_query_yes_no,
                                                                                mock_call,
                                                                                mock_connect_to_wireless_adb):
        mock_call.side_effect = [1, 1, 0]  # First call: fail. Second call: success
        mock_query_yes_no.return_value = True
        mock_query_yes_no_call = mock.call("Did you reconnect the device?")

        with MockStdout() as mock_stdout:
            unreachable_device_fix(self.connection)
            self._verify_message_printed_to_user(mock_stdout.getvalue())
            mock_query_yes_no.assert_has_calls([mock_query_yes_no_call, mock_query_yes_no_call])
            mock_connect_to_wireless_adb.assert_called()

    @mock.patch(TESTED_MODULE_NAME + ".connect_to_wireless_adb")
    @mock.patch(TESTED_MODULE_NAME + ".subprocess.call")
    @mock.patch(TESTED_MODULE_NAME + ".query_yes_no")
    def test_unreachable_device_fix__user_gave_up__user_is_prompted_no_connection(self, mock_query_yes_no,
                                                                                  mock_call,
                                                                                  mock_connect_to_wireless_adb):
        mock_call.return_value = 1
        mock_query_yes_no.side_effect = [True, True, False]
        mock_query_yes_no_call = mock.call("Did you reconnect the device?")

        with MockStdout() as mock_stdout:
            unreachable_device_fix(self.connection)
            self._verify_message_printed_to_user(mock_stdout.getvalue())
            mock_query_yes_no.assert_has_calls([mock_query_yes_no_call, mock_query_yes_no_call, mock_query_yes_no_call])
            mock_connect_to_wireless_adb.assert_not_called()

    @mock.patch(TESTED_MODULE_NAME + ".connect_to_wireless_adb")
    @mock.patch(TESTED_MODULE_NAME + ".subprocess.call")
    @mock.patch(TESTED_MODULE_NAME + ".query_yes_no")
    def test_unreachable_device_fix__initial_ping_success__nothing_is_done(self, mock_query_yes_no,
                                                                           mock_call,
                                                                           mock_connect_to_wireless_adb):
        mock_call.return_value = 0

        with MockStdout() as mock_stdout:
            unreachable_device_fix(self.connection)
            self._verify_message_not_printed_to_user(mock_stdout.getvalue())
            mock_query_yes_no.assert_not_called()
            mock_connect_to_wireless_adb.assert_not_called()

    @mock.patch(TESTED_MODULE_NAME + ".connect_to_wireless_adb")
    @mock.patch(TESTED_MODULE_NAME + ".subprocess.call")
    @mock.patch(TESTED_MODULE_NAME + ".query_yes_no")
    def test_unreachable_device_fix__connection_is_wired__no_ping_done(self, mock_query_yes_no, mock_call,
                                                                       mock_connect_to_wireless_adb):
        self.connection.device_id = u"BH9003KE51"

        with MockStdout() as mock_stdout:
            unreachable_device_fix(self.connection)
            self._verify_message_not_printed_to_user(mock_stdout.getvalue())

        mock_call.assert_not_called()
        mock_query_yes_no.assert_not_called()
        mock_connect_to_wireless_adb.assert_not_called()

    def _verify_message_printed_to_user(self, stdout):
        self.assertIn("Device is not reachable.", stdout)
        self.assertIn("Please reconnect the device to the network.", stdout)

    def _verify_message_not_printed_to_user(self, stdout):
        self.assertNotIn("Device is not reachable.", stdout)
        self.assertNotIn("Please reconnect the device to the network.", stdout)
