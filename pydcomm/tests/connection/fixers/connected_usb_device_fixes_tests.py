import __builtin__
import unittest

import mock

from pydcomm.general_android.connection.fixers.connected_usb_device_fixes import get_connected_usb_devices, \
    get_connected_phones, no_device_connected_init_fix, \
    no_device_connected_adb_fix
from pydcomm.tests.helpers import TestCasePatcher, MockStdout

MODULE_NAME = "pydcomm.general_android.connection.fixers.connected_usb_device_fixes"


class NoDeviceConnectedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.patcher = TestCasePatcher(self)
        self.mock_check_output = self.patcher.addPatch(MODULE_NAME + ".subprocess.check_output")
        self.mock_raw_input = self.patcher.addObjectPatch(__builtin__, "raw_input")

    def test_get_connected_usb_devices__normal_input__get_proper_devices(self):
        self.mock_check_output.return_value = """Bus 002 Device 003: ID 0424:5744 Standard Microsystems Corp. 
Bus 002 Device 002: ID 0b95:1790 ASIX Electronics Corp. AX88179 Gigabit Ethernet
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 0424:2514 Standard Microsystems Corp. USB 2.0 Hub
Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver

"""
        self.assertEqual(get_connected_usb_devices(),
                         [('0424', '5744'),
                          ('0b95', '1790'),
                          ('1d6b', '0003'),
                          ('0424', '2514'),
                          ('046d', 'c52b')])

    def test_get_connected_phones__normal_input__get_proper_devices(self):
        self.mock_check_output.return_value = """Bus 002 Device 003: ID 0424:5744 Standard Microsystems Corp. 
Bus 002 Device 002: ID 0b95:1790 ASIX Electronics Corp. AX88179 Gigabit Ethernet
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 0424:2514 Standard Microsystems Corp. USB 2.0 Hub
Bus 001 Device 082: ID 2a70:4ee7  
Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
Bus 001 Device 067: ID 040d:3410 VIA Technologies, Inc. 
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 061: ID 0fce:51d9 Sony Ericsson Mobile Communications AB 

"""
        self.assertEqual(get_connected_phones(), ['Sony Ericsson', 'OnePlus'])

    def test_no_device_connected_adb_fix__device_is_connected__nothing_is_written_to_the_user(self):
        self.mock_check_output.return_value = """Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
Bus 001 Device 067: ID 040d:3410 VIA Technologies, Inc. 
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 061: ID 0fce:51d9 Sony Ericsson Mobile Communications AB 
"""
        with MockStdout() as mock_stdout:
            connection = mock.Mock()
            no_device_connected_init_fix(connection, "")
            no_device_connected_adb_fix(connection)
            self.assertFalse(mock_stdout.getvalue())

    def test_no_device_connected_adb_fix__device_was_disconnected__appropriate_message_written(self):
        self.mock_check_output.side_effect = ["""Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
Bus 001 Device 067: ID 040d:3410 VIA Technologies, Inc. 
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 061: ID 0fce:51d9 Sony Ericsson Mobile Communications AB 
""",
                                              """Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
                                              Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
                                              Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
                                              Bus 001 Device 067: ID 040d:3410 VIA Technologies, Inc. 
                                              Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
                                              """]
        with MockStdout() as mock_stdout:
            connection = mock.Mock()
            no_device_connected_init_fix(connection, "")
            no_device_connected_adb_fix(connection)
            self.assertIn("Sony Ericsson", mock_stdout.getvalue())
            self.mock_raw_input.assert_called_once()

    def test_no_device_connected_adb_fix__unknown_device_was_disconnected__appropriate_message_written(self):
        self.mock_check_output.side_effect = ["""Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
Bus 001 Device 067: ID 040d:3410 VIA Technologies, Inc. 
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 061: ID 0fce:51d9 Sony Ericsson Mobile Communications AB 
""",
                                              """Bus 001 Device 005: ID 046d:c52b Logitech, Inc. Unifying Receiver
                                              Bus 001 Device 004: ID 045e:07a5 Microsoft Corp. Wireless Receiver 1461C
                                              Bus 001 Device 002: ID 0424:2744 Standard Microsystems Corp. 
                                              Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
                                              Bus 003 Device 061: ID 0fce:51d9 Sony Ericsson Mobile Communications AB 
                                                                                            """]
        with MockStdout() as mock_stdout:
            connection = mock.Mock()
            no_device_connected_init_fix(connection, "")
            no_device_connected_adb_fix(connection)
            self.assertTrue(mock_stdout.getvalue())
            self.mock_raw_input.assert_called_once()
