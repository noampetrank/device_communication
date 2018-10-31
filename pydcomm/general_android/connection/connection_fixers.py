import subprocess32 as subprocess


def add_rooted_impl(connection, device_id=None):
    connection._run_adb("root")
    connection._run_adb("remount")


# region Auto fixes

def restart_adb_server_fix(connection):
    subprocess.check_call(["adb", "kill-server"])
    subprocess.check_call(["adb", "start-server"])


def set_usb_mode_to_mtp_fix(connection):
    connection._run_adb(["shell", "setprop sys.usb.config \"mtp,adb\""])


# endregion Auto fixes

# region Manual fixes



# endregion Manual fixes
