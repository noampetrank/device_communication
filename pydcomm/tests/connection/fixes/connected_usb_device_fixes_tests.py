import unittest

import mock


class NoDeviceConnectedRecoveryTests(unittest.TestCase):
    pass
# @mock.patch("pydcomm.general_android.connection.connection_fixers.subprocess.check_output")
# # https://stackoverflow.com/a/31171719/365408
# @mock.patch("pydcomm.general_android.connection.connection_fixers.sys.stdout", new_callable=StringIO)
#     def test__no_device_disconnected__no_message_shown(self, mock_check_output):
#         # arrange
#         mock_connection_cls = mock.Mock()
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
# pass
