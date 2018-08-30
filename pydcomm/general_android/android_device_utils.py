import datetime
import re
import numpy as np
import logging

log = logging.getLogger(__name__)


class AndroidDeviceUtilsError(Exception):
    pass  # General error class for device utils


class AndroidDeviceUtils:
    """
    Class exposing basic operations on an android device.
    Methods here control the device itself and not a specific app.
    Some methods may have to be overriden for a specific model,
    mainly due to differences in return values of adb commands
    """
    def __init__(self, connection):
        """
        :type connection: AdbConnection
        """
        self.connection = connection

    def push(self, local_path, path_on_device):
        """
        Push a file/dir to the device.
        :type local_path: str
        :type path_on_device: str
        :rtype: bool
        """
        lines, ok = self.connection.adb("push {} {}".format(local_path, path_on_device).split())
        if not ok:
            log.warn("error in device utils push:", lines)
            return False
        return any('files pushed' in r for r in lines)

    def pull(self, path_on_device, local_path):
        """
        Pull a file/dir to the device.
        :type path_on_device: str
        :type local_path: str
        :rtype: bool
        """
        lines, ok = self.connection.adb("push {} {}".format(path_on_device, local_path).split())
        if not ok:
            log.warn("error in device utils pull:", lines)
            return False
        return any('files pulled' in r for r in lines)

    def _get_intent_type_code(self, param):
        """
        return intent "Type" string according to type of param
        :param param:
        :rtype: str
        """
        cur_type = type(param)
        if cur_type is int:
            return "--ei"
        elif cur_type in [float, np.float64]:
            return "--ef"
        else:  # for now we will default to string
            return "--es"

    def _expand_intent_params_into_list(self, **params):
        """
        Transform params to a list of str containing --ei/--ef etc.
        :type options: dict[str: str]
        :return: list[str]
        """
        res = []
        for key, value in params.iteritems():
            res.append(key)
            res.append(self._get_intent_type_code(value))
            res.append(str(value))
        return res

    def send_intent(self, action, name, *params_list):
        """
        see also: expand_intent_params_into_list() for convenience
        :type action:  str ('start', 'force-stop')
        :type name: str
        :type args: dict[str, str]
        """
        return self._shell("am", "broadcast", "-a", name, self._expand_intent_params_into_list(params_list))[0]

    def _shell(self, *args):
        """
        :type args: list(str)
        """
        log.info("_shell params:", *args)
        return self.connection.adb("shell", *args)

    def mkdir(self, path_on_device):
        """
        create a folder on the device
        :type path_on_device: str
        :rtype: bool
        """
        lines, ok = self._shell("mkdir", path_on_device)
        # in case of lines, nothing is printed...
        return ok and len(lines) == 0

    def rmdir(self, path_on_device):
        """
        remove a folder on the device
        :type path_on_device: str
        :rtype: bool
       """
        lines, ok = self._shell("rm", "-rf", path_on_device)
        # in case of lines, nothing is printed...
        return ok and len(lines) == 0

    def touch_file(self, path_on_device):
        """
        touch a file on the device
        :type path_on_device: str
        """
        lines, ok = self._shell("touch", path_on_device)
        # in case of lines, nothing is printed...
        return ok and len(lines) == 0

    def remove(self, path_on_device):
        """
        remove a file from the device
        :type path_on_device: str
        """
        lines, ok = self._shell("rm", "-f", path_on_device)
        # in case of success, nothing is printed...
        return ok and len(lines) == 0

    def ls(self, path_on_device):
        """
        According to ls -lat output: drwxrwx---   9 system cache     4096 2018-05-16 03:00 cache
        For files with permissions error, ret['permissions'] (and all other flelds except name) will be None.
        MIGHT BE DEVICE SPECIFIC (UNLIKELY)
        :type path_on_device: str
        :rtype list[dict[permissons, n_links, owner, group, size, modified, name]]
        """
        lines, _ = self._shell("ls", "-lat", path_on_device)
        lines = [l for l in lines if (not l.startswith("total") and not l.endswith("."))]
        res = []
        for l in lines:
            vals = l.split()
            if len(vals) != 8:
                log.error("Error in ls: unexpected number of values in the line", l)
                raise AndroidDeviceUtilsError("Incorrect string returned from ls: " + l)
            res.append({'permissions': vals[0],
                        'n_links': vals[1],
                        'owner': vals[2],
                        'group': vals[3],
                        'size': vals[4],
                        'modified': ' '.join([vals[5], vals[6]]),
                        'name': vals[7]})
        return res

    def get_time(self):
        """
        :rtype: datetime
        """
        lines, ok = self._shell('date', '+"%Y-%m-%d\\', '%H:%M:%S:%N"')
        if not ok:
            raise AndroidDeviceUtilsError("failed to get device time")
        return datetime.datetime.strptime(lines[0], '%Y-%m-%d %H:%M:%S:%f')

    def get_device_name(self):
        """
        return the BUGATONE device name (used in recording scripts)
        :rtype: str
        """
        name, success = self._shell("cat", "/data/local/tmp/devicename")
        if success:
            return name[-1]
        else:
            raise AndroidDeviceUtilsError("failed to get device name")

    def get_prop(self, prop_name):
        """
        get a value of device property
        :type prop_name: str
        :rtype: str
        """
        res, ok = self._shell("getprop", prop_name)
        if not ok:
            msg = "failed to get value of property: " + prop_name
            log.error(msg)
            raise AndroidDeviceUtilsError(msg)
        elif len(res) == 0:
            msg = "property not found on the device: " + prop_name
            log.error(msg)
            raise AndroidDeviceUtilsError(msg)
        return res[-1]

    def set_prop(self, prop_name, value):
        """
        set a value of a device property.
        this method has no return value, so we return nothing
        :type prop_name: str
        :type value: str
        """
        self._shell("setprop", prop_name, value)

    def reboot(self):
        """
        reboot the device
        """
        self.connection.adb("reboot")

    def _check_earphone_connected(self, dumpsys_output):
        """
        parse the dumpsys audio and check if an earphone is connected
        QUITE POSSIBLY DEVICE SPECIFIC
        :type dumpsys_output: str
        :rtype: bool
        """
        device = re.findall(r'STREAM_MUSIC.*?Devices: (\w+)', dumpsys_output, re.DOTALL)[0]
        return device.lower() in 'headset'

    def _check_device_volume(self, dumpsys_output):
        """
        parse the dumpsys audio and check for device stream volume
        QUITE POSSIBLY DEVICE SPECIFIC
        :type dumpsys_output: str
        :rtype: bool
        """
        device = re.findall(r'STREAM_MUSIC.*?Devices: (\w+)', dumpsys_output, re.DOTALL)[0]
        return int(re.findall(r'- STREAM_MUSIC.*?{}\): (\d+)'.format(device), dumpsys_output, re.DOTALL)[0])

    def is_earphone_connected(self):
        """
        :rtype: bool
        """
        txt, _ = self._shell('dumpsys', 'audio')
        return self._check_earphone_connected(txt)

    def get_volume(self):
        """
        :rtype: int
        """
        txt, _ = self._shell('dumpsys', 'audio')
        return self._check_device_volume(txt)

    def set_volume(self, val):
        """
        set the stream volume on the device
        :type val: int
        :rtype: bool
        """
        if val > self.get_max_volume():
            return False
        self._shell("service", "call", "audio", "3", "i32", "3", "i32", str(val), "i32", "0")
        return val == self.get_volume()

    def is_max_volume(self):
        """
        :rtype: bool
        """
        return self.get_volume() == self.get_max_volume()

    def get_max_volume(self):
        """
        get the max volume supported on the device
        device specific for sure
        :rtype: int
        """
        raise NotImplementedError()