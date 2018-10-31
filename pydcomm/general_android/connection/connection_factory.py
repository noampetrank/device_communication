from pydcomm.general_android.connection.device_selector import add_choose_first_behavior, add_user_choice_behavior, MultiDeviceBehavior
from pydcomm.general_android.connection.wired_adb_connection import AdbConnection
from pydcomm.general_android.connection.wireless_adb_connection import add_connect_wireless


# Save AdbConnection functions that can be decorated in order to allow resetting the class
AdbConnection.original_init = AdbConnection.__init__
AdbConnection.original_adb = AdbConnection.adb


# TODO: Add tests
class AdbConnectionFactory(object):
    # TODO: Add helper method for oppo devices.
    @staticmethod
    def create_connection(wired=False, ip=None, device=None, decorators=None, device_selector=MultiDeviceBehavior.CHOOSE_FIRST):
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

        decorators.append(AdbConnectionFactory.get_selection_behavior(device_selector))

        # Reset AdbConnection decorated functions
        AdbConnection.__init__ = AdbConnection.original_init
        AdbConnection.adb = AdbConnection.original_adb

        con_cls = AdbConnection
        if not wired:
            con_cls = add_connect_wireless(con_cls)
        for d in decorators:
            con_cls = d(con_cls)

        con = con_cls(ip or device)
        return con

    @staticmethod
    def get_selection_behavior(device_selector):
        if device_selector == MultiDeviceBehavior.CHOOSE_FIRST:
            return add_choose_first_behavior
        elif device_selector == MultiDeviceBehavior.USER_CHOICE:
            return add_user_choice_behavior
        else:
            raise ValueError("Received invalid device_selector")
