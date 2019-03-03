from pydcomm.public.iconnection import CommandFailedError
from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix


# region Auto fixes

def restart_adb_server_fix(connection):
    connection.adb("kill-server", specific_device=False, disable_fixers=True, timeout=1)
    connection.adb("start-server", specific_device=False, disable_fixers=True, timeout=10)


def set_usb_mode_to_mtp_fix(connection):
    try:
        connection.adb("shell setprop sys.usb.config \"mtp,adb\"", disable_fixers=True, timeout=2)
        adb_connect_fix(connection)
        print("Mtp fix succeded. Please report to Ziv.")
    except CommandFailedError:
        # This always fails since the phone is not authorized.
        pass


def manually_set_usb_mode_to_mtp_fix(connection):
    print("Please make sure the device is connected with a cable. "
          "Then set USB mode to 'Transfer Files' and press ENTER")
    raw_input()
    adb_connect_fix(connection)

# endregion Auto fixes
