import subprocess

from enum import IntEnum
import logging

log = logging.getLogger(__name__)


class Connection:
    """
    Connects to a device and maintains the connection.
    """

    def __init__(self, device_id=None):
        """
        :type device_id: str
        """
        # Connect to device
        self.device_id = device_id
        self.fixes = []
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
        :return: -
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
        :type args: list[str]
        :param args: array of split args to adb command
        :rtype: tuple(list(str), bool)
        """
        if not self._test_connection():
            self._handle_error()
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


# region Connection decorators
# TODO: this region could go to a separate file(s), e.g. connection_fixes.py

def add_rooted(connection):
    # make connection also rooted
    # modify "connect" function
    # ...
    return connection


def add_automated_recovery(connection):
    # ...
    return connection


def add_interactive_troubleshooting_recovery(connection):
    # ...
    return connection


def add_choose_first_device(connection):
    # ...
    return connection


def add_user_device_choise(connection):
    # ...
    return connection


def add_samsung_quirks(connection):
    # add samsung special fixes to connection
    # modify "connect" function
    # ...
    return connection


# endregion


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


class ConnectionFactory:
    def get_rooted_wireless_interactive_connection(self):
        """
        Returns a connection for rooted (Oppo) devices that communicates wirelessly to the phone
         and when the phone disconnects asks the user for action to help reconnect the phone.
        """
        return self.get_connection(rooted=True, automated_recovery=True, interactive_recovery=True)

    def get_rooted_wireless_automated_connection(self):
        """
        Returns a connection for rooted (Oppo) devices that communicates wirelessly to the phone
         and when the phone disconnects it automatically tries to reconnect and if it can't it throws an exception.
        """
        return self.get_connection(rooted=True, automated_recovery=True, interactive_recovery=False)

    def get_samsung_automated_connection(self):
        """
        If for some reason connecting to Samsung devices is different (eg. it doesn't require wifi, or
        it has some special automated recovery), this function wll create the connection.
        """
        return self.get_connection(automated_recovery=True, interactive_recovery=True, special_samsung=True)

    def get_connection(self, rooted=False, automated_recovery=False, interactive_recovery=False, special_samsung=False, multi_device=MultiDeviceBehavior.CHOOSE_FIRST):
        con = Connection()
        if automated_recovery:
            # con.fixes.append(reboot_connection)
            con = add_automated_recovery(con)
        if interactive_recovery:
            con = add_interactive_troubleshooting_recovery(con)
        if rooted:
            con = add_rooted(con)
        if special_samsung:
            con = add_samsung_quirks(con)
        if multi_device == MultiDeviceBehavior.CHOOSE_FIRST:
            con = add_choose_first_device(con)
        elif multi_device == MultiDeviceBehavior.USER_CHOICE:
            con = add_user_device_choise(con)
        return con
