from pydcomm.general_android.connection.connection_fixers import restart_adb_server_fix, \
    set_usb_mode_to_mtp_fix, manually_set_usb_mode_to_mtp_fix
from pydcomm.general_android.connection.decorator_helpers import add_fixers
from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix
from pydcomm.general_android.connection.fixers.connected_usb_device_fixes import forgot_device_fix, device_turned_off
from pydcomm.general_android.connection.fixers.enable_usb_debugging_fixer import enable_usb_debugging_fix
from pydcomm.general_android.connection.fixers.get_user_attention_fixer import get_user_attention_fix
from pydcomm.general_android.connection.fixers.unreachable_device_fixer import unreachable_device_fix
from pydcomm.general_android.connection.internal_adb_connection import InternalAdbConnection
from pydcomm.general_android.connection.wireless_adb_connection import add_connect_wireless, add_disconnect_wireless


class InternalAdbConnectionFactory(object):
    @staticmethod
    def create_connection(wired=False, ip=None, device=None, fixers=None):
        """
        Create a connection to the given ip or device, add the given fixers
        :param wired: Connect wired or wireless
        :param ip: If given and connecting wireless, connect to this IP
        :param device: If given, connect to this USB device
        :param list[(connection) -> None] fixers: A list of fixer functions
        :return
        """
        fixers = fixers or []

        con_cls = InternalAdbConnection
        if not wired:
            con_cls = add_connect_wireless(con_cls)
            con_cls = add_disconnect_wireless(con_cls)

        con_cls = add_fixers(con_cls, "adb", fixers)

        con = con_cls(ip or device, filter_wireless_devices=wired)
        return con

    @staticmethod
    def get_oppo_wireless_device(use_manual_fixes=True, device_id=None):
        fixers = []
        fixers.append(adb_connect_fix)
        if use_manual_fixes:
            # get_user_attention_fix must be the first manual fixer.
            fixers.append(get_user_attention_fix)
            fixers.append(device_turned_off)
            fixers.append(enable_usb_debugging_fix)
            fixers.append(unreachable_device_fix)

        return InternalAdbConnectionFactory.create_connection(wired=False, fixers=fixers, device=device_id)

    @staticmethod
    def get_oppo_wired_device(use_manual_fixes=True, device_id=None):
        fixers = []
        fixers.append(set_usb_mode_to_mtp_fix)
        fixers.append(restart_adb_server_fix)

        if use_manual_fixes:
            # get_user_attention_fix must be the first manual fixer.
            fixers.append(get_user_attention_fix)
            fixers.append(manually_set_usb_mode_to_mtp_fix)
            fixers.append(forgot_device_fix)
            fixers.append(enable_usb_debugging_fix)
            fixers.append(device_turned_off)

        return InternalAdbConnectionFactory.create_connection(wired=True, fixers=fixers, device=device_id)
