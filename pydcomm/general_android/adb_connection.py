import subprocess

from enum import IntEnum
import logging

log = logging.getLogger(__name__)

from general_android.adb_connection_decorators import add_adb_recovery_decorator, auto_fixes, add_rooted_impl


class AdbConnectionError(Exception):
    pass  # General error class for ADB connection


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
        return dict(
            is_connected=self._test_connection(),
            is_wireless=None,  # TODO
            connection_type=None,
            device_id=None,
        )

    def disconnect(self):
        """
        Disconnect from the device
        """
        pass

    def _test_connection(self):
        return subprocess.check_output("adb shell echo hi").strip() == "hi"

    def adb(self, *params):
        """
        Send the given command over adb.
        :type params: list[str]
        :param params: array of split args to adb command
        :rtype: tuple(str, bool)
        """
        log.info("adb params:", *params)

        if params[0] is 'adb':
            log.warn("adb() called with 'adb' as first parameter. Is this intentional?")

        try:
            return subprocess.check_output(params), True
        except subprocess.CalledProcessError as err:
            # log the exception
            log.error("adb returned with the following error code, returning output and False", err.returncode, err.message)
            return err.output, False

    @staticmethod
    def restart_adb_server():
        """
        adb kill-server & adb start-start
        """
        def _run_and_check(cmd):
            if subprocess.call(cmd.split()) != 0:
                raise AdbConnectionError('Could not restart ADB server')
        _run_and_check('adb kill-server')
        _run_and_check('adb start-server')


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
