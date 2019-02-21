import re
import subprocess

from enum import IntEnum
from pybuga.infra.utils.user_input import UserInput


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


def add_choose_first_behavior(connection):
    """
    Decorates the _get_device_to_connect method with the choose first behavior.
    :type filter_wireless_devices: bool
    :type connection: InternalAdbConnection
    :rtype: InternalAdbConnection
    """

    def _get_device_to_connect(self, filter_wireless_devices=False):
        devices = adb_devices(filter_wireless_devices)
        if not devices:
            raise EnvironmentError("No devices connected")
        return devices[0][1]

    connection._get_device_to_connect = _get_device_to_connect
    return connection


def get_device_to_connect_user_choice(filter_wireless_devices=False):
    devices = adb_devices(filter_wireless_devices)
    while not devices:
        UserInput.text("Please connect a device with a cable, choose 'Transfer files' USB mode and press ENTER.",
                       lambda x: True)
        devices = adb_devices(filter_wireless_devices)
    print("Please select a device")
    choice = UserInput.menu(([(x[1], x[2]) for x in devices]))
    return choice


def add_user_choice_behavior(connection):
    """
    Decorates the _get_device_to_connect method with the user choice behavior.
    :type connection: InternalAdbConnection
    :rtype: InternalAdbConnection
    """

    connection._get_device_to_connect = get_device_to_connect_user_choice
    return connection


def adb_devices(filter_wireless_devices=False):
    def parse_line(line):
        device_id, status = line.split("\t")
        if "no permissions" in status or "unauthorized" in status:
            status = "no permissions"
        if re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4}\b", device_id):
            connection_type = "wireless"
        else:
            connection_type = "wired"
        return connection_type, device_id, status.strip()

    output = subprocess.check_output(["adb", "devices"])
    if not output.startswith("List of devices attached"):
        raise ValueError("Unexpected output from \"adb devices\"")

    return [parse_line(x) for x in output.splitlines()[1:] if
            x and not (filter_wireless_devices and parse_line(x)[0] == "wireless")]
