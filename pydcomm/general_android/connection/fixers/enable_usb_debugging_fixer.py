from __future__ import print_function

from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix


def enable_usb_debugging_fix(connection):
    print("Please enable USB debugging on the device and press ENTER")
    raw_input()
    if not connection.wired:
        adb_connect_fix(connection)
