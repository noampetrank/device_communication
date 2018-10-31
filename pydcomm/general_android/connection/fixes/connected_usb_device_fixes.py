import re

import subprocess32 as subprocess


def get_connected_usb_devices():
    out = subprocess.check_output("lsusb")
    return re.findall(r"Bus \d+ Device \d+: ID (\w{4}):(\w{4})", out)


def get_connected_phones():
    all_devices = get_connected_usb_devices()
    vendor_ids = [x[0] for x in all_devices]
    phone_vendor_ids = [x[0] for x in known_phone_usb_ids if x[1].lower() in vendor_ids]
    return phone_vendor_ids


def not_device_connected_init_fix(connection):
    connection._initial_usb_list = get_connected_usb_devices()


def not_device_connected_adb_fix(connection):
    connected_usbs = get_connected_usb_devices()
    difference = list(set(connection._initial_usb_list) - set(connected_usbs))
    vendor_ids = [x[0] for x in difference]
    phone_vendor_ids_disconnected = [x[0] for x in known_phone_usb_ids if x[1].lower() in vendor_ids]
    for i in phone_vendor_ids_disconnected:
        print("A phone from manufacturer {} has been disconnected, is this your device?".format(i))
        raw_input()
    if len(phone_vendor_ids_disconnected) != len(vendor_ids):
        print("A usb device has been disconnected, is this the phone?")
        raw_input()


def forgot_device_fix(connection):
    if not get_connected_phones():
        print("I can't see any phone connected, is the phone connected?")
    else:
        print("Are you sure the phone is connected?")
    raw_input()


def device_turned_off(connection):
    if get_connected_phones():
        print("There is a phone connected, is it turned on? Is USB debugging enabled?")
    else:
        print("Is the phone turned on?")
    raw_input()


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