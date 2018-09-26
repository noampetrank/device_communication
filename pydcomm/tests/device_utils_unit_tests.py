import datetime
import unittest
from textwrap import dedent

import mock
import tempfile

from pydcomm.general_android.connection.wired_adb_connection import AdbConnection, AdbConnectionError
from pydcomm.general_android.android_device_utils import AndroidDeviceUtils, LocalFileNotFound, RemoteFileNotFound, WrongPermissions, FileAlreadyExists, OperationUnsupported, \
    AndroidDeviceUtilsError


class UnitTestDeviceUtils(unittest.TestCase):
    def setUp(self):
        """
        Executed in the beginning of each test
        """
        self.conn = mock.Mock()
        self.device_utils = AndroidDeviceUtils(self.conn)

    def tearDown(self):
        """
        Executed in the end of each test
        """
        pass

    # region AndroidDeviceUtils.push() unit tests

    def test_push_ok(self):
        self.conn.adb.return_value = '[100%] /sdcard/tmpANxMOd\n/tmp/tmpANxMOd: 1 file pushed. 0.0 MB/s (61 bytes in 0.011s)\n'
        with tempfile.NamedTemporaryFile() as tmp_file:
            content = 'The quick brown fox jumps over the lazy dog\n1234567890\n\01234\x1234'
            tmp_file.write(content)
            tmp_file.flush()
            self.device_utils.push(tmp_file.name, '/sdcard/')

    def test_push_from_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "adb: error: cannot stat '/home/buga/tmp_dir/tmp_file.tm': No such file or directory\n"
        self.conn.adb.side_effect = err
        self.assertRaises(LocalFileNotFound, self.device_utils.push, '/home/buga/tmp_dir/tmp_file.tm', '/sdcard/')

    def test_push_to_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "[100%] /sdcard23/\nadb: error: failed to copy '/home/buga/tmp_dir/tmp_file.tmp' to '/sdcard23/': remote couldn't create file: Is a directory\n/home/buga/tmp_dir/tmp_file.tmp: 0 files pushed. 0.0 MB/s (44 bytes in 0.003s)\n"
        self.conn.adb.side_effect = err
        self.assertRaises(RemoteFileNotFound, self.device_utils.push, '/home/buga/tmp_dir/tmp_file.tmp', '/sdcard23/')

    def test_push_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = "[100%] /tmp_file.tmp\nadb: error: failed to copy '/home/buga/tmp_dir/tmp_file.tmp' to '/tmp_file.tmp': remote couldn't create file: Read-only file system\n/home/buga/tmp_dir/tmp_file.tmp: 0 files pushed. 0.0 MB/s (44 bytes in 0.005s)\n"
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.push, '/home/buga/tmp_dir/tmp_file.tmp', '/')

    # endregion

    # region AndroidDeviceUtils.pull() unit tests

    def test_pull_ok(self):
        self.conn.adb.return_value = '[100%] /sdcard/tmp_file.tmp\n/sdcard/tmp_file.tmp: 1 file pulled. 0.0 MB/s (44 bytes in 0.003s)\n'
        self.device_utils.pull('/sdcard/tmp_file.tmp', '/home/buga/tmp_dir/')


    def test_pull_from_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "adb: error: failed to stat remote object '/sdcard/tmp_file.tm': No such file or directory\n"
        self.conn.adb.side_effect = err
        self.assertRaises(RemoteFileNotFound, self.device_utils.pull, '/sdcard/tmp_file.tm', '/home/buga/tmp_dir/')

    def test_pull_to_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "adb: error: cannot create '/home/buga/tmp_dir2/': Is a directory\n"
        self.conn.adb.side_effect = err
        self.assertRaises(LocalFileNotFound, self.device_utils.pull, '/sdcard/tmp_file.tmp', '/home/buga/tmp_dir2/')

    def test_pull_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = "adb: error: cannot create '/home/buga/tmp_dir/no_perm/tmp_file.tmp': Permission denied\n"
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.pull, '/sdcard/tmp_file.tmp', '/home/buga/tmp_dir/no_perm')

    # endregion

    # region AndroidDeviceUtils.send_intent() unit tests

    def test_send_intent_ok(self):
        self.conn.adb.return_value = 'Broadcasting: Intent { act=INTENT_ACTION_NAME flg=0x400000 }\nBroadcast completed: result=0\n'
        self.device_utils.send_intent('start', 'INTENT_ACTION_NAME')

    # endregion

    # region AndroidDeviceUtils._shell() unit tests

    def test_shell_ok(self):
        self.conn.adb.return_value = 'hi\n'
        self.assertEqual(self.device_utils._shell('echo hi').strip(), 'hi')

    # endregion

    # region AndroidDeviceUtils.mkdir() unit tests

    def test_mkdir_ok(self):
        self.conn.adb.return_value = ''
        self.device_utils.mkdir('/sdcard/tmp_dir')

    def test_mkdir_already_exists(self):
        err = AdbConnectionError()
        err.stderr = "mkdir: '/sdcard/tmp_dir/': File exists\n"
        self.conn.adb.side_effect = err
        self.assertRaises(FileAlreadyExists, self.device_utils.mkdir, '/sdcard/tmp_dir')

    def test_mkdir_in_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "mkdir: '/sdcard/tmp_dir/sub/dir': No such file or directory\n"
        self.conn.adb.side_effect = err
        self.assertRaises(RemoteFileNotFound, self.device_utils.mkdir, '/sdcard/tmp_dir/sub/dir')

    def test_mkdir_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = "mkdir: '/system/tmp_dir': Read-only file system\n"
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.mkdir, '/system/tmp_dir')

    # endregion

    # region AndroidDeviceUtils.rmdir() unit tests

    def test_rmdir_ok(self):
        self.conn.adb.return_value = ''
        self.device_utils.rmdir('/sdcard/tmp_dir')

    def test_rmdir_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = 'rm: /system/tmp_dir: No such file or directory\n'
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.rmdir, '/system/tmp_dir')

    # endregion

    # region AndroidDeviceUtils.touch_file() unit tests

    def test_touch_file_ok(self):
        self.conn.adb.return_value = ''
        self.device_utils.touch_file('/sdcard/tmp_file2')

    def test_touch_file_in_non_existent(self):
        err = AdbConnectionError()
        err.stderr = "touch: '/sdcard/notexist/tmp_file2': No such file or directory\n"
        self.conn.adb.side_effect = err
        self.assertRaises(RemoteFileNotFound, self.device_utils.touch_file, '/sdcard/notexist/tmp_file2')

    def test_touch_file_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = "touch: '/system/tmp_file': Read-only file system\n"
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.touch_file, '/system/tmp_file')

    # endregion

    # region AndroidDeviceUtils.remove() unit tests

    def test_remove_ok(self):
        self.conn.adb.return_value = ''
        self.device_utils.remove('/sdcard/tmp_file.tmp')

    def test_remove_no_permissions(self):
        err = AdbConnectionError()
        err.stderr = 'rm: /system/tmp_file: No such file or directory\n'
        self.conn.adb.side_effect = err
        self.assertRaises(WrongPermissions, self.device_utils.remove, '/system/tmp_file')

    # endregion

    # region AndroidDeviceUtils.ls() unit tests

    def test_ls_ok(self):
        stdout = dedent("""\
            total 32216
            drwxr-xr-x  2 root shell    8192 2008-12-31 20:30 .
            -rwxr-xr-x  1 root shell   47760 2008-12-31 20:30 ATFWD-daemon
            -rwxr-xr-x  1 root shell   61232 2008-12-31 20:30 BCM4345C0_003.001.025.0138.0222.HCD
            -rwxr-xr-x  1 root shell   52870 2008-12-31 20:30 BCM4358A3_001.004.015.0076.0130_0x66_ORC.HCD
            -rwxr-xr-x  1 root shell   22720 2008-12-31 20:30 WifiLogger_app
            lrwxr-xr-x  1 root shell       6 2008-12-31 20:30 acpi -> toybox
            -rwxr-xr-x  1 root shell    6264 2008-12-31 20:30 adsprpcd
            -rwxr-xr-x  1 root shell     210 2008-12-31 20:30 am
            lrwxr-xr-x  1 root shell      13 2008-12-31 20:30 app_process -> app_process64
            lrwxr-xr-x  1 root shell       6 2008-12-31 20:30 xargs -> toybox
            lrwxr-xr-x  1 root shell       6 2008-12-31 20:30 xxd -> toybox
            lrwxr-xr-x  1 root shell       6 2008-12-31 20:30 yes -> toybox
            -rwxr-xr-x  1 root shell   67704 2008-12-31 20:30 yuvtool
            drwxr-xr-x 19 root root     4096 1970-01-01 02:00 ..
            """)
        stderr = dedent("""\
            ls: /system/bin/PktRspTest: Permission denied
            ls: /system/bin/StoreKeybox: Permission denied
            ls: /system/bin/xtwifi-inet-agent: Permission denied
            """)

        self.conn.adb.return_value = stdout
        ls = self.device_utils.ls('/system/bin')
        self.assertEqual(len([x for x in ls if x['links_to']]), 5)
        self.assertEqual(len(ls), 14)

        err = AdbConnectionError()
        err.stdout = stdout
        err.stderr = stderr
        self.conn.adb.side_effect = err
        ls = self.device_utils.ls('/system/bin')
        self.assertEqual(len([x for x in ls if x['links_to']]), 5)
        self.assertEqual(len([x for x in ls if x['permissions'] is None]), 3)
        self.assertEqual(len(ls), 17)
        self.assertIn(dict(permissions='drwxr-xr-x', n_links=2, owner='root', group='shell', size=8192, modified=datetime.datetime(2008, 12, 31, 20, 30), name='.', links_to=None), ls)
        self.assertIn(dict(permissions='lrwxr-xr-x', n_links=1, owner='root', group='shell', size=6, modified=datetime.datetime(2008, 12, 31, 20, 30), name='acpi', links_to='toybox'), ls)
        self.assertIn(dict(permissions=None, n_links=None, owner=None, group=None, size=None, modified=None, name='PktRspTest', links_to=None), ls)

    def test_ls_doesnt_exist(self):
        err = AdbConnectionError()
        err.stderr = 'ls: /abc: No such file or directory\n'
        self.conn.adb.side_effect = err
        self.assertRaises(RemoteFileNotFound, self.device_utils.ls, '/abc')

    # endregion

    # region AndroidDeviceUtils.get_time() unit tests

    def test_get_time_ok(self):
        stdout = "2018-09-09\\ 11:18:04:348158411\n"
        self.conn.adb.return_value = stdout
        device_time = self.device_utils.get_time()
        expected_time = datetime.datetime(2018, 9, 9, 11, 18, 4, 348158)
        self.assertEquals(device_time, expected_time)

    # endregion

    # region AndroidDeviceUtils.remove() unit tests

    def test_remove_ok(self):
        path = '/sdcard/somefile'
        stdout = "\n"
        self.conn.adb.return_value = stdout
        self.device_utils.remove(path)

    def test_remove_non_existent(self):
        # TODO: Invoke device_utils.remove(path) where 'path' doesn't exist and expect a RemoteFileNotFound exception
        pass

    def test_remove_no_permissions(self):
        # TODO: Invoke device_utils.remove(path) where 'path' has no write permissions and expect WrongPermissions exception
        pass

    # endregion

    # region AndroidDeviceUtils.get_device_name() unit tests

    def test_get_device_name_ok(self):
        dne = "oppo845H_24bits_17"
        self.conn.adb.return_value = dne
        dna = self.device_utils.get_device_name()
        self.assertEqual(dne, dna)

    def test_get_device_name_unsupported(self):
        err = AdbConnectionError()
        err.stderr = 'rm: /data/local/tmp/devicename: No such file or directory\n'
        self.conn.adb.side_effect = err
        self.assertRaises(OperationUnsupported, self.device_utils.get_device_name)

    # endregion

    # region AndroidDeviceUtils.get_prop() unit tests

    def test_get_prop_ok(self):
        pe = "testtesttest"
        self.conn.adb.return_value = pe
        pa = self.device_utils.get_prop("testprop")
        self.assertEqual(pe, pa)

    # endregion

    # region AndroidDeviceUtils.set_prop() unit tests

    def test_set_prop_ok(self):
        def check_adb_input(*args):
            self.assertTrue(args[-1][0] == '"' and args[-1][-1] == '"', 'setprop value should be wrapped in "double quotes" to keep whitespaces')
        self.conn.adb.side_effect = check_adb_input
        self.device_utils.set_prop("testprop", ' a b c ')

    # endregion

    # region AndroidDeviceUtils.is_earphone_connected() unit tests

    OPPO_DUMPSYS_AUDIO = dedent("""\
        - STREAM_RING:
           Muted: true
           Min: 0
           Max: 16
           Current: 2 (speaker): 0, 40000000 (default): 14
           Devices: speaker, headset
        - STREAM_MUSIC:
           Muted: false
           Min: 0
           Max: 16
           Current: 2 (speaker): 16, 4 (headset): 8, 8 (headphone): 8, 40000000 (default): 10
           Devices: headset
        - STREAM_ALARM:
           Muted: false
           Min: 1
           Max: 16
           Current: 40000000 (default): 12
           Devices: speaker, headset
        """)

    def test_is_earphone_connected_true_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO
        self.assertTrue(self.device_utils.is_earphone_connected())

    def test_is_earphone_connected_false_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO.replace('headset', 'boombox')
        self.assertFalse(self.device_utils.is_earphone_connected())

    def test_is_earphone_connected_fail(self):
        self.conn.adb.return_value = ""
        self.assertRaises(AndroidDeviceUtilsError, self.device_utils.is_earphone_connected)

    # endregion

    # region AndroidDeviceUtils.get_volume() unit tests

    def test_get_volume_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO
        self.assertEqual(self.device_utils.get_volume(), 8)

    def test_get_volume_fail(self):
        self.conn.adb.return_value = ""
        self.assertRaises(AndroidDeviceUtilsError, self.device_utils.get_volume)

    # endregion

    # region AndroidDeviceUtils.set_volume() unit tests

    def test_set_volume_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO.replace('8', '5')
        self.device_utils.set_volume(5)

    def test_set_volume_fail(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO.replace('8', '5')
        self.assertRaises(AndroidDeviceUtilsError, self.device_utils.set_volume, 6)

    # endregion

    # region AndroidDeviceUtils.is_max_volume() unit tests

    def test_is_max_volume_true_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO.replace('8', '16')
        self.assertTrue(self.device_utils.is_max_volume())

    def test_is_max_volume_false_ok(self):
        self.conn.adb.return_value = UnitTestDeviceUtils.OPPO_DUMPSYS_AUDIO
        self.assertFalse(self.device_utils.is_max_volume())

    # endregion
