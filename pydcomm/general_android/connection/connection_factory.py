from pydcomm.general_android.connection.connection_fixers import add_rooted_impl, restart_adb_server_fix, \
    set_usb_mode_to_mtp_fix, manually_set_usb_mode_to_mtp_fix
from pydcomm.general_android.connection.decorator_helpers import add_init_decorator, add_adb_recovery_decorator
from pydcomm.general_android.connection.device_selector import add_choose_first_behavior, add_user_choice_behavior, \
    MultiDeviceBehavior
from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix
from pydcomm.general_android.connection.fixers.call_a_developer_fixer import call_a_developer_fix
from pydcomm.general_android.connection.fixers.connected_usb_device_fixes import forgot_device_fix, device_turned_off
from pydcomm.general_android.connection.fixers.enable_usb_debugging_fixer import enable_usb_debugging_fix
from pydcomm.general_android.connection.fixers.get_user_attention_fixer import get_user_attention_fix
from pydcomm.general_android.connection.fixers.unreachable_device_fixer import unreachable_device_fix
from pydcomm.general_android.connection.fixers.verify_same_network_fixer import verify_same_network_fix
from pydcomm.general_android.connection.wired_adb_connection import InternalAdbConnection
from pydcomm.general_android.connection.wireless_adb_connection import add_connect_wireless, add_disconnect_wireless

# Save InternalAdbConnection functions that can be decorated in order to allow resetting the class
InternalAdbConnection.original_init = InternalAdbConnection.__init__
InternalAdbConnection.original_adb = InternalAdbConnection.adb
InternalAdbConnection.original_disconnect = InternalAdbConnection.disconnect


class AdbConnectionFactory(object):
    @staticmethod
    def create_connection(wired=False, ip=None, device=None, decorators=None):
        """
        Create a connection to the given ip or device, add the given decorators
        :param wired: Connect wired or wireless
        :param ip: If given and connecting wireless, connect to this IP
        :param device: If given, connect to this USB device
        :param decorators: A list of decorators to apply on the connection
        :param device_selector: A strategy to select the device to connect to
        :type device_selector: MultiDeviceBehavior
        :return
        """
        decorators = decorators or []

        # Reset InternalAdbConnection decorated functions
        InternalAdbConnection.__init__ = InternalAdbConnection.original_init
        InternalAdbConnection.disconnect = InternalAdbConnection.original_disconnect
        InternalAdbConnection.adb = InternalAdbConnection.original_adb

        con_cls = InternalAdbConnection
        if not wired:
            con_cls = add_connect_wireless(con_cls)
            con_cls = add_disconnect_wireless(con_cls)
        for d in decorators:
            con_cls = d(con_cls)

        con = con_cls(ip or device, filter_wireless_devices=wired)
        return con

    @staticmethod
    def get_oppo_wireless_device(use_manual_fixes=True, rooted=True, device_id=None):
        decorators = []

        if rooted:
            decorators.append(add_init_decorator(add_rooted_impl))

        if use_manual_fixes:
            # call_a_developer_fix must be the first manual fixer
            decorators.append(add_adb_recovery_decorator(call_a_developer_fix))
            decorators.append(add_adb_recovery_decorator(verify_same_network_fix))
            decorators.append(add_adb_recovery_decorator(device_turned_off))
            decorators.append(add_adb_recovery_decorator(enable_usb_debugging_fix))
            decorators.append(add_adb_recovery_decorator(unreachable_device_fix))
            decorators.append(add_adb_recovery_decorator(manually_set_usb_mode_to_mtp_fix))
            # get_user_attention_fix must be the last manual fixer.
            decorators.append(add_adb_recovery_decorator(get_user_attention_fix))

        decorators.append(add_adb_recovery_decorator(set_usb_mode_to_mtp_fix))
        decorators.append(add_adb_recovery_decorator(adb_connect_fix))
        return AdbConnectionFactory.create_connection(wired=False, decorators=decorators, device=device_id)

    @staticmethod
    def get_oppo_wired_device(use_manual_fixes=True, rooted=True, device_id=None):
        decorators = []

        if rooted:
            decorators.append(add_init_decorator(add_rooted_impl))

        if use_manual_fixes:
            # call_a_developer_fix must be the first manual fixer
            decorators.append(add_adb_recovery_decorator(call_a_developer_fix))
            decorators.append(add_adb_recovery_decorator(device_turned_off))
            decorators.append(add_adb_recovery_decorator(enable_usb_debugging_fix))
            decorators.append(add_adb_recovery_decorator(forgot_device_fix))
            decorators.append(add_adb_recovery_decorator(manually_set_usb_mode_to_mtp_fix))
            # get_user_attention_fix must be the last manual fixer.
            decorators.append(add_adb_recovery_decorator(get_user_attention_fix))

        decorators.append(add_adb_recovery_decorator(restart_adb_server_fix))
        decorators.append(add_adb_recovery_decorator(set_usb_mode_to_mtp_fix))
        return AdbConnectionFactory.create_connection(wired=True, decorators=decorators, device=device_id)
