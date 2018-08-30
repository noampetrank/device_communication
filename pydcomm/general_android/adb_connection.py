import subprocess

from enum import IntEnum
import logging

log = logging.getLogger(__name__)

from general_android.adb_connection_decorators import add_adb_recovery_decorator, auto_fixes, add_rooted_impl


class AdbConnection:
    """
    Connects to a device and maintains the connection.
    """

    def __init__(self, device_id=None):
        """
        :type device_id: str
        """
        pass

    def get_connection_status(self):
        """
        :return: dict object with the following fields:
            is_connected: bool
            is_wireless: bool
            connection_type: string in ('usb_debugging', 'mtp', 'file_transfer')
            device_id: string
        """
        pass

    def disconnect(self):
        """
        Disconnect from the device
        """
        pass

    def _test_connection(self):
        return self.check_output("adb shell echo hi") == "hi"

    def _handle_error(self):
        for f in self.fixes:
            f()
            if self._test_connection():
                break

    def adb(self, *args):
        """
        Send the given command over adb.
        :type args: list[str]
        :param args: array of split args to adb command
        :rtype: tuple(list(str), bool)
        """
        if not self._test_connection():
            self._handle_error()
        log.info("adb params:", *args)

        args = list(args)
        if args[0] is not 'adb':
            args = ['adb'] + args
        try:
            return subprocess.check_output(args).splitlines(), True
        except subprocess.CalledProcessError as err:
            # log the exception
            log.error("adb return with the following error code, returning output and False", err.returncode, err.message)
            return err.output.splitlines(), False

    @staticmethod
    def restart_adb_server():
        """
        adb kill-server & adb start-start
        """
        pass


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


class AdbConnectionFactory(object):
    def get_rooted_auto_connection(self, device):
        return self.create_connection(device=device, decorators=[add_rooted_impl, add_adb_recovery_decorator(auto_fixes)])

    @staticmethod
    def create_connection(ip=None, device=None, decorators=None, device_selector=None):
        """
        Create a connection to the given ip or device, add the given decorators
        :param ip:
        :param device:
        :param decorators:
        :type device_selector: MultiDeviceBehavior
        :return:
        """
        con = AdbConnection(ip or device)
        for d in decorators or []:
            con = d(con)

        return con
