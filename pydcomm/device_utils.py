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

    @staticmethod
    def expand_intent_params(**params):
        """
        Transform params to a list of str containing --ei/--ef etc.
        :type options: dict[str: str]
        :return: list[str]
        """
        pass

    def send_intent(self, action, name, *params_list):
        """
        :type action:  str ('start', 'force-stop')
        :type name: str
        :type args: dict[str, str]
        :return:
        """
        self.connection.adb("am" + command)
        pass

    def _shell(self, *args):
        """
        :type args: list(str)
        """
        self.send_intent("myaction",frequency=float(freq),action_od=int(action_id))
        self.send_intent("myaction",[("frequency",float,(freq)),action_od=int(action_id)])

        pass

    def do_ac_sthing(self,param1,param2,param3):
        param1 = float(param1)
        param2 = str(param2)
        param3 = int(param3)
        self.connection.send_intent("asdasd",param1,param2,param3)

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
        According to la -lat output: drwxrwx---   9 system cache     4096 2018-05-16 03:00 cache
        For files with permissions error, ret['permissions'] (and all other filelds except name) will be None.
        :type path_on_device: list[dict[permissons, n_links, owner, group, size, modified, name]]
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

    def get_prop(self, prop_name):
        """
        :type prop_name: str
        :rtype: str
        """

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
