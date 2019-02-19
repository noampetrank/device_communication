from __future__ import print_function

from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix


def verify_same_network_fix(connection):
    print("Please make sure the device and your computer are on the same network and press ENTER")
    raw_input()
    adb_connect_fix(connection)
