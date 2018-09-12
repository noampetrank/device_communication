from pydcomm.general_android.connection.device_selector import add_choose_first_behavior, add_user_choice_behavior, MultiDeviceBehavior


class AdbConnectionFactory(object):
    @staticmethod
    def create_connection(wired=False, ip=None, device=None, decorators=None, device_selector=MultiDeviceBehavior.CHOOSE_FIRST):
        """
        Create a connection to the given ip or device, add the given decorators
        :param ip:
        :param device:
        :param decorators:
        :type device_selector: MultiDeviceBehavior
        :return
        """
        decorators = decorators or []

        decorators.append(AdbConnectionFactory.get_selection_behavior(device_selector))

        if wired:
            con_cls = WiredAdbConnection
        else:
            con_cls = WirelessAdbConnection
        con = con_cls(ip or device)
        for d in decorators or []:
            con = d(con)

        return con

    @staticmethod
    def get_selection_behavior(device_selector):
        if device_selector == MultiDeviceBehavior.CHOOSE_FIRST:
            return add_choose_first_behavior
        elif device_selector == MultiDeviceBehavior.USER_CHOICE:
            return add_user_choice_behavior
        else:
            raise ValueError("Received invalid device_selector")
