from device_utils import DeviceUtils


class OppoDeviceUtils(DeviceUtils):
    """
    Implementation for Oppo 845 devices
    """

    def __init__(self, connection):
        DeviceUtils.__init__(self, connection)

    def get_max_volume(self):
        return 16
