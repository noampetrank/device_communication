from pydcomm.general_android.connection.device_selector import add_choose_first_behavior, add_user_choice_behavior, MultiDeviceBehavior
from pydcomm.general_android.connection.adb_connection import AdbConnection, add_connect_wireless


class AdbConnectionFactory(object):
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
