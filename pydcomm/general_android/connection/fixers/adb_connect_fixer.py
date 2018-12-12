from __future__ import print_function
from pydcomm.general_android.connection.wired_adb_connection import ConnectingError
from pydcomm.general_android.connection.wireless_adb_connection import connect_to_wireless_adb


def adb_connect_fix(connection):
    try:
        print("Trying to connect to device")
        connect_to_wireless_adb(connection,"")
    except ConnectingError:
        print("Failed to connect to device")
        pass
