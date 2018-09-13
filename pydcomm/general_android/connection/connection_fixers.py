import logging

import subprocess32 as subprocess
import re


def add_rooted_impl(connection):
    connection.adb("root")
    connection.adb("remount")
    return connection


def add_adb_recovery_decorator(fix_function, fix_name):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, *params):
            if not self.test_connection():
                try:
                    fix_function(self)
                except Exception as e:
                    self.log.warn("Fix {} failed ".format(fix_name), exc_info=e)
            return old_adb(self, *params)

        connection.adb = new_adb
        return connection

    return inner


# region Auto fixes
def restart_adb_server_fix(connection):
    subprocess.check_call(["adb", "kill-server"])
    subprocess.check_call(["adb", "start-server"])


def set_usb_mode_to_mtp_fix(connection):
    subprocess.check_call(["adb", "shell", "setprop sys.usb.config \"mtp,adb\""])


# endregion

# region Manual fixes

known_phone_usb_ids = [
    ("2a70", "OnePlus"),
    ("22d9", "Oppo"),
    ("18d1", "Google")
]


def add_no_device_connected_recovery(connection):
    old_init = connection.__init__
    old_adb = connection.adb

    def get_connected_usb_devices():
        out = subprocess.check_output("lsusb")
        return re.findall(r"Bus \d+ Device \d+: ID (\w{4}):(\w{4})", out)

    def replace_init(self, device_id=None):
        old_init(self, device_id)
        a = get_connected_usb_devices()
        self._initial_usb_list = a

    def replace_adb(self, *params):
        if not self.test_connection():
            connected_usbs = get_connected_usb_devices()
            if connected_usbs != self._initial_usb_list:
                print("Is the device connected to the computer?")
        return old_adb(self, *params)

    connection.__init__ = replace_init
    connection.adb = replace_adb
    return connection


def no_device_connected_init(device_id=None):
    pass


def no_device_connected(connection):
    lsusb_output = subprocess.check_output("lsusb")
    pass
# endregion
