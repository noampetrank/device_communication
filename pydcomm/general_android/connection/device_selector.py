import re

from enum import IntEnum
from pybuga.infra.utils.user_input import UserInput


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


def add_choose_first_behavior(connection):
    """
    Decorates the _get_device_to_connect method with the choose first behavior.
    :type connection: AdbConnection
    :rtype: AdbConnection
    """

    def _get_device_to_connect(self):
        devices = adb_devices(self)
        if not devices:
            raise EnvironmentError("No devices connected")
        return devices[0][1]

    connection._get_device_to_connect = _get_device_to_connect
    return connection


def add_user_choice_behavior(connection):
    """
    Decorates the _get_device_to_connect method with the user choice behavior.
    :type connection: AdbConnection
    :rtype: AdbConnection
    """

    def _get_device_to_connect(self):
        devices = adb_devices(self)
        while not devices:
            UserInput.text("No devices connected. Please connect a device and press enter.", lambda x: True)
            devices = adb_devices(self)
        print("Please select a device")
        choice = UserInput.menu(([(x[1], x[2]) for x in devices]))
        return choice

    connection._get_device_to_connect = _get_device_to_connect
    return connection


def adb_devices(connection):
    def parse_line(line):
        device_id, status = line.split("\t")
        if "no permissions" in status or "unauthorized" in status:
            status = "no permissions"
        if re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4}\b", device_id):
            connection_type = "wireless"
        else:
            connection_type = "wired"
        return connection_type, device_id, status.strip()

    output = connection.adb("devices", timeout=1, specific_device=False, disable_fixers=True)
    if not output.startswith("List of devices attached"):
        raise ValueError("Unexpected output from \"adb devices\"")

    return [parse_line(x) for x in output.splitlines()[1:] if x]
