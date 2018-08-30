import unittest
import mock
import tempfile
import numpy as np

from general_android.adb_connection import AdbConnection
from general_android.android_device_utils import AndroidDeviceUtils


@mock.patch.object(AdbConnection, 'adb')
class UnitTestDeviceUtils(unittest.TestCase):

    def setUp(self):
        """
        Executed in the beginning of each test
        """
        self.conn = AdbConnection()
        self.device_utils = AndroidDeviceUtils(self.conn)

    def tearDown(self):
        """
        Executed in the end of each test
        """
        pass

    # region AndroidDeviceUtils.push() unit tests

    def test_push_ok(self, mock_adb):
        mock_adb.return_value = ('[100%] /sdcard/tmpANxMOd\n/tmp/tmpANxMOd: 1 file pushed. 0.0 MB/s (61 bytes in 0.011s)\n', True)
        with tempfile.NamedTemporaryFile() as tmp_file:
            content = 'The quick brown fox jumps over the lazy dog\n1234567890\n\01234\x1234'
            tmp_file.write(content)
            tmp_file.flush()
            ret = self.device_utils.push(tmp_file.name, '/sdcard/')
            assert ret

    def test_push_from_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.push(from, to) where 'from' doesn't exist and expect a LocalFileNotFound exception
        pass

    def test_push_to_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.push(from, to) where 'to' path doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_push_no_permissions(self, mock_adb):
        # TODO: Invoke device_utils.push(from, to) where 'to' has no write permissions and expect WrongPermissions exception
        pass

    # endregion

    # region AndroidDeviceUtils.pull() unit tests

    def test_pull_ok(self, mock_adb):
        # TODO: Invoke device_utils.pull(from, to) and expect no exceptions and no output.
        pass

    def test_pull_from_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.pull(from, to) where 'from' doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_pull_to_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.pull(from, to) where 'to' path doesn't exist and expect a LocalFileNotFound exception
        pass

    def test_pull_no_permissions(self, mock_adb):
        # TODO: Invoke device_utils.pull(from, to) where 'from' has no write permissions and expect WrongPermissions exception
        pass

    # endregion

    # region AndroidDeviceUtils.send_intent() unit tests

    def test_send_intent_ok(self, mock_adb):
        # TODO: Invoke device_utils.intent() and expect no exceptions and no output.
        pass

    # endregion

    # region AndroidDeviceUtils._shell() unit tests

    def test_shell_ok(self, mock_adb):
        # TODO: assert(device_utils._shell('echo hi')=='hi')
        pass

    # endregion

    # region AndroidDeviceUtils.mkdir() unit tests

    def test_mkdir_ok(self, mock_adb):
        # TODO: Invoke device_utils.mkdir(path) and expect no exceptions and no output.
        pass

    def test_mkdir_in_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.mkdir(path) where path base doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_mkdir_no_permissions(self, mock_adb):
        # TODO: Invoke device_utils.mkdir(path) where path has no write permissions and expect WrongPermissions exception
        pass

    # endregion

    # region AndroidDeviceUtils.touch_file() unit tests

    def test_touch_file_ok(self, mock_adb):
        # TODO: Invoke device_utils.touch_file(path) and expect no exceptions and no output.
        pass

    def test_touch_file_in_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.touch_file(path) where path base doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_touch_file_no_permissions(self, mock_adb):
        # TODO: Invoke device_utils.touch_file(path) where path has no write permissions and expect WrongPermissions exception
        pass


    # endregion

    # region AndroidDeviceUtils.ls() unit tests

    def test_ls_ok(self, mock_adb):
        # TODO: Invoke device_utils.ls('/') and check there is a 'system' folder in the output. Parse the format of each field and verify it's corrent.
        pass

    def test_ls_doesnt_exist(self, mock_adb):
        # TODO: Invoke device_utils.ls('/sggfjdhgdjf') and expect a RemoteFileNotFound exception
        pass

    def test_ls_doesnt_wrong_permissions(self, mock_adb):
        # TODO: Invoke device_utils.ls(no_read_permissions_path) and expect a WrongPermissions exception (is this possible?)
        pass

    # endregion

    # region AndroidDeviceUtils.get_time() unit tests

    def test_get_time_ok(self, mock_adb):
        # TODO: Invoke device_utils.get_time() and parse output.
        pass

    # endregion

    # region AndroidDeviceUtils.remove() unit tests

    def test_remove_ok(self, mock_adb):
        # TODO: Invoke device_utils.remove(path) and expect no exceptions and no output.
        pass

    def test_remove_non_existent(self, mock_adb):
        # TODO: Invoke device_utils.remove(path) where 'path' doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_remove_no_permissions(self, mock_adb):
        # TODO: Invoke device_utils.remove(path) where 'path' has no write permissions and expect WrongPermissions exception
        pass

    # endregion

    # region AndroidDeviceUtils.get_device_name() unit tests

    def test_get_device_name_ok(self, mock_adb):
        # TODO: Invoke device_utils.get_device_name() and parse output.
        pass

    def test_get_device_name_unsupported(self, mock_adb):
        # TODO: Invoke device_utils.get_device_name() on a device that doesn't support this operation and expect OperationUnsupported exception.
        pass

    # endregion

    # region AndroidDeviceUtils.get_prop() unit tests

    def test_get_prop_ok(self, mock_adb):
        # TODO: Invoke device_utils.get_prop('xxx') and expect no exceptions and no output.
        pass

    # endregion

    # region AndroidDeviceUtils.set_prop() unit tests

    def test_set_prop_ok(self, mock_adb):
        # TODO: Invoke device_utils.set_prop('xxx', '123') and expect no exceptions and no output (meaning that get_prop verified the value that was set).
        pass

    def test_set_prop_fail(self, mock_adb):
        # TODO: Invoke device_utils.set_prop('xxx', '123') and expect OperationFailed exception (meaning that get_prop got the wrong value).
        pass

    # endregion
    
    # region AndroidDeviceUtils.reboot() unit tests

    def test_reboot_ok(self, mock_adb):
        # TODO: Invoke device_utils.reboot() and expect the connection to be lost in a few seconds.
        pass

    def test_reboot_fail(self, mock_adb):
        # TODO: Invoke device_utils.reboot() and expect OperationFailed exception (meaning that the phone doesn't disconnect after a few secs).
        pass

    # endregion

    # region AndroidDeviceUtils.is_earphone_connected() unit tests

    def test_is_earphone_connected_true_ok(self, mock_adb):
        # TODO: Invoke device_utils.is_earphone_connected() and expect True result.
        pass

    def test_is_earphone_connected_false_ok(self, mock_adb):
        # TODO: Invoke device_utils.is_earphone_connected() and expect False result.
        pass

    def test_is_earphone_connected_fail(self, mock_adb):
        # TODO: Invoke device_utils.is_earphone_connected() and expect OperationFailed exception (meaning that the output from `adb shell dumpsys audio` is wrong)
        pass

    # endregion

    # region AndroidDeviceUtils.get_volume() unit tests

    def test_get_volume_ok(self, mock_adb):
        # TODO: Invoke device_utils.get_volume() and expect a number from 0 to 16.
        pass

    def test_get_volume_fail(self, mock_adb):
        # TODO: Invoke device_utils.get_volume() and expect OperationFailed exception (meaning that the output from `adb shell dumpsys audio` is wrong)
        pass

    # endregion

    # region AndroidDeviceUtils.set_volume() unit tests

    def test_set_volume_ok(self, mock_adb):
        # TODO: Invoke device_utils.set_volume() and expect no exceptions and no output. (meaning get_volume() verified the value)
        pass

    def test_set_volume_fail(self, mock_adb):
        # TODO: Invoke device_utils.set_volume() and expect OperationFailed exception (meaning that the output from `adb shell dumpsys audio` has a number different from what was set)
        pass

    # endregion

    # region AndroidDeviceUtils.is_max_volume() unit tests

    def test_is_max_volume_true_ok(self, mock_adb):
        # TODO: Invoke device_utils.is_max_volume() and expect True result.
        pass

    def test_is_max_volume_false_ok(self, mock_adb):
        # TODO: Invoke device_utils.is_max_volume() and expect False result.
        pass

    # endregion


