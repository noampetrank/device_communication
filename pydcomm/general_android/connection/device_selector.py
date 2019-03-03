import os
import re
import subprocess
from ConfigParser import ConfigParser, NoOptionError
from collections import OrderedDict
from warnings import warn

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


def store_all_devices_serials_in_cache(i_am_michael=False):
    """
    Stores serial number to name mapping for all currently connected devices in cache.
    Don't forget to commit the cache file after this.
    :param bool i_am_michael: Explains itself, doesn't it? If not, ask Michael.
    :return: None
    """
    if not i_am_michael:
        raise Exception("You are not michael!")
    for conn_type, device_id, status in adb_devices():
        if conn_type == "wired" and status == "device":
            device_id_to_device_name(device_id, i_am_michael_and_i_want_to_store_serial_in_cache=i_am_michael)


def device_id_to_device_name(device_id, is_wireless=False, i_am_michael_and_i_want_to_store_serial_in_cache=False):
    """
    Convert device id to name.
    For wired devices, will try to find the mapping in the cache file.
    Then will ask the device itself.
    :param str device_id: device serial number or IP address
    :param bool is_wireless: wired or wireless connection
    :param bool i_am_michael_and_i_want_to_store_serial_in_cache: Store serial number to name mapping in cache. Michael will do that for new devices. See store_all_devices_serials_in_cache.
    :return str: device name
    """
    # Get device name from the cache
    cfg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "device_serial_to_name_mapping.ini"))
    cfg = ConfigParser()
    cfg.read(cfg_path)
    try:
        device_name = cfg.get("mapping", device_id)
    except NoOptionError:
        device_name = None

    # Get device name from the device itself
    if not device_name or i_am_michael_and_i_want_to_store_serial_in_cache:
        if not device_name and not is_wireless and not i_am_michael_and_i_want_to_store_serial_in_cache:
            warn("Couldn't find {} device in {}".format(device_id, cfg_path))

        try:
            # device_utils = AndroidDeviceUtils(InternalAdbConnection(device_id, filter_wireless_devices=False))
            # device_name = device_utils.get_device_name()
            device_name = subprocess.check_output("adb -s {} shell cat /data/local/tmp/devicename".format(device_id), shell=True, stderr=subprocess.PIPE).strip()

            if i_am_michael_and_i_want_to_store_serial_in_cache:
                if device_name:
                    cfg.set("mapping", device_id, device_name)
                    with open(cfg_path, 'w') as configfile:
                        cfg.write(configfile)
                else:
                    raise Exception("Couldn't get device name for {} device!".format(device_id))
        except:
            pass

    # Finally if we still don't have the device name, return the device_id
    if not device_name:
        device_name = device_id

    # Make sure strings don't use unicode (this is because UserInput.menu doesn't work well with unicode)
    return device_name.encode('charmap') if device_name is not None else None


def get_device_to_connect_user_choice(filter_wireless_devices=False):
    devices = adb_devices(filter_wireless_devices)
    while not devices:
        UserInput.text("No devices detected. Please do the following:\n"
                       "1. Connect a device with a cable.\n"
                       "2. Enable USB debugging.\n"
                       "3. Choose 'Transfer files' USB mode.\n"
                       "4. Press ENTER.",
                       lambda x: True)
        devices = adb_devices(filter_wireless_devices)

    devices = sorted(devices, key=lambda x: x[0], reverse=True)  # This will make 'wireless' appear before 'wired'
    device_name_to_id = OrderedDict()
    for conn_type, device_id, _ in devices:
        if device_id not in device_name_to_id:
            device_name = device_id_to_device_name(device_id, conn_type == "wireless")
            device_name_to_id[device_name] = device_id

    print("Please select a device")
    choice = UserInput.menu(device_name_to_id.keys())
    return device_name_to_id[choice]


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
