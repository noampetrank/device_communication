from enum import IntEnum

from pydcomm.connection_decorators import add_some_recovery, auto_fixes, manual_fixes, add_rooted_impl


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

    def adb(self, params):
        """
        Send the given command over adb.
        :type params: list[str]
        :param params: array of splitted args to adb command
        """
        pass

    @staticmethod
    def restart_adb_server():
        """
        adb kill-server & adb start-start
        """
        pass


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


class ConnectionFactory(object):
    def get_rooted_auto_connection(self, device):
        return self.create_connection(device=device, decorators=[add_rooted_impl, add_some_recovery(auto_fixes)])

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
