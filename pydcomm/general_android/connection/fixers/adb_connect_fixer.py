from __future__ import print_function

from pydcomm.general_android.connection.wired_adb_connection import ConnectingError
from pydcomm.general_android.connection.wireless_adb_connection import adb_connect


def adb_connect_fix(connection):
    from pydcomm.general_android.connection.connection_fixers import restart_adb_server_fix
    try:
        print("Trying to connect to device")
        restart_adb_server_fix(connection)
        adb_connect(connection)
    except ConnectingError:
        print("Failed to connect to device")
