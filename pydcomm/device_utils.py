from connection import Connection


class DeviceUtils:
    def __init__(self, connection):
        """
        :type connection: Connection
        """
        self.connection = connection


    ## Probably non-device specific ##

    def push(self, local_path, path_on_device):
        """
        Push a file/dir to the device.
        :type local_path: str
        :type path_on_device: str
        """
        pass

    def pull(self, path_on_device, local_path):
        """
        Pull a file/dir to the device.
        :type path_on_device: str
        :type local_path: str
        """
        pass

    def send_intent(self, action, name, **args):
        """
        :type action:  str
        :type name: str
        :type args: dict[str, str]
        :return:
        """
        pass

    def shell(self, *args):
        """
        :type args: list(str)
        """
        pass

    def mkdir(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def touch_file(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def ls(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def get_time(self):
        """
        :rtype: datetime
        """
        pass

    def remove(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def get_device_name(self):
        """
        :rtype: str
        """
        pass

    def set_prop(self, prop_name, value):
        """
        :type prop_name: str
        :type value: str
        """
        pass

    def reboot(self):
        """
        """
        pass


    ## Possibly device specific ##

    def is_earphone_connected(self):
        """
        :rtype: bool
        """
        pass

    def get_volume(self):
        """
        :rtype: int
        """
        pass

    def set_volume(self, val):
        """
        :type val: int
        """
        pass

    def is_max_volume(self):
        """
        :rtype: bool
        """
        pass
