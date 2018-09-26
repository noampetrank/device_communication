from pydcomm.general_android.android_device_utils import AndroidDeviceUtils


class OppoDeviceUtils(AndroidDeviceUtils):
    """
    Implementation for Oppo 845 devices
    """

    def __init__(self, connection):
        AndroidDeviceUtils.__init__(self, connection)

    def get_max_volume(self):
        return 16
