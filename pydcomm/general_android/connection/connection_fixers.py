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

# List taken from https://android.googlesource.com/platform/system/core/+/android-5.1.1_r38/adb/usb_vendors.c
# The list is old, incomplete, and abandoned by Google https://stackoverflow.com/q/52352442/365408
known_phone_usb_ids = [
    ('Acer', '0502'),
    ('Allwinner', '1F3A'),
    ('Amlogic', '1b8e'),
    ('AnyDATA', '16D5'),
    ('Archos', '0E79'),
    ('Asus', '0b05'),
    ('BYD', '1D91'),
    ('Compal', '04B7'),
    ('Compalcomm', '1219'),
    ('Dell', '413c'),
    ('ECS', '03fc'),
    ('EMERGING_TECH', '297F'),
    ('Emerson', '2207'),
    ('Foxconn', '0489'),
    ('Fujitsu', '04C5'),
    ('Funai', '0F1C'),
    ('Garmin-Asus', '091E'),
    ('Gigabyte', '0414'),
    ('Gigaset', '1E85'),
    ('GIONEE', '271D'),
    ('Google', '18d1'),
    ('Haier', '201E'),
    ('Harris', '19A5'),
    ('Hisense', '109b'),
    ('Honeywell', '0c2e'),
    ('HP', '03f0'),
    ('HTC', '0bb4'),
    ('Huawei', '12D1'),
    ('INQ Mobile', '2314'),
    ('Intel', '8087'),
    ('Intermec', '067e'),
    ('IRiver', '2420'),
    ('K-Touch', '24E3'),
    ('KT Tech', '2116'),
    ('Kobo', '2237'),
    ('Kyocera', '0482'),
    ('Lab126', '1949'),
    ('Lenovo', '17EF'),
    ('LenovoMobile', '2006'),
    ('LG', '1004'),
    ('Lumigon', '25E3'),
    ('Motorola', '22b8'),
    ('MSI', '0DB0'),
    ('MTK', '0e8d'),
    ('NEC', '0409'),
    ('B&N Nook', '2080'),
    ('Nvidia', '0955'),
    ('OPPO', '22D9'),
    ('On-The-Go-Video', '2257'),
    ('OUYA', '2836'),
    ('Pantech', '10A9'),
    ('Pegatron', '1D4D'),
    ('Philips', '0471'),
    ('Panasonic Mobile Communication', '04DA'),
    ('Positivo', '1662'),
    ('Prestigio', '29e4'),
    ('Qisda', '1D45'),
    ('Qualcomm', '05c6'),
    ('Quanta', '0408'),
    ('Rockchip', '2207'),
    ('Samsung', '04e8'),
    ('Sharp', '04dd'),
    ('SK Telesys', '1F53'),
    ('Smartisan', '29a9'),
    ('Sony', '054C'),
    ('Sony Ericsson', '0FCE'),
    ('T & A Mobile Phones', '1BBB'),
    ('TechFaith', '1d09'),
    ('Teleepoch', '2340'),
    ('Texas Instruments', '0451'),
    ('Toshiba', '0930'),
    ('Unowhy', '2A49'),
    ('Vizio', 'E040'),
    ('Wacom', '0531'),
    ('Xiaomi', '2717'),
    ('YotaDevices', '2916'),
    ('Yulong Coolpad', '1EBF'),
    ('ZTE', '19D2')
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
            difference = list(set(self._initial_usb_list) - set(connected_usbs))
            vendor_ids = [x[0] for x in difference]
            phone_vendor_ids_disconnected = [x[0] for x in known_phone_usb_ids if x[1].lower() in vendor_ids]
            for i in phone_vendor_ids_disconnected:
                print("A phone from manufacturer {} has been disconnected, please reconnect".format(i))
                raw_input()
            if len(phone_vendor_ids_disconnected) != len(vendor_ids):
                print("A usb device has been disconnected, is this the phone?")
                raw_input()
        return old_adb(self, *params)

    connection.__init__ = replace_init
    connection.adb = replace_adb
    return connection

# endregion
