import re

import subprocess32 as subprocess
from pydcomm.general_android.connection.wired_adb_connection import ConnectingError
from pydcomm.general_android.connection.decorator_helpers import add_init_decorator
from subprocess32 import CalledProcessError


def get_device_ip(device_id):
    """
    get the ip address of the connected device.
    :return: ip. None if device is not connected to wifi
    """
    ifconfig = subprocess.check_output('adb -s {} shell ifconfig'.format(device_id).split(" "))
    ips = re.findall(r"wlan0.*\n.*inet addr:(\d+\.\d+\.\d+\.\d+)", ifconfig)
    if ips:
        return ips[0]
    else:
        return None


def _run_with_exception(command, exception_message):
    try:
        subprocess.check_call(command)
    except CalledProcessError:
        raise ConnectingError(exception_message)


def connect_wireless(self, device_id=None):
    """
    This is a decorator over WiredAdbConnection, it adds a connection to wireless after the regular connection has been established.
    It is transformed later into a decorator called `add_connect_wireless`.
    :param self: AdbConnection
    :param device_id:
    """
    if not self.test_connection():
        raise ConnectingError("No device connected to PC")
    ip = get_device_ip(device_id or self.device_id)
    # TODO: Test that the ip is in the same subnet
    if not ip:
        raise ConnectingError("Device is not connected to wifi")
    else:
        self.device_serial = self.device_id
        self.device_id = ip
    # TODO: Possibly need to change to mtp mode
    _run_with_exception("adb tcpip 5555".split(" "), "Failed to change to tcp mode")
    _run_with_exception("adb connect {}:5555".format(self.device_id).split(" "), "Can't connect to ip {}".format(self.device_id))
    print("Device is connected over wifi, disconnect and press enter to continue.")
    # TODO: This needs to be in a fixer.
    # raw_input()
    # _run_with_exception("adb connect {}:5555".format(self.device_id).split(" "), "Can't connect to ip {}".format(self.device_id))


add_connect_wireless = add_init_decorator(connect_wireless, "connect_wireless")
