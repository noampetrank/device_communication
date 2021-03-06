import datetime
import re
import numpy as np
import subprocess

from pydcomm import DcommError
from pydcomm.public.iconnection import CommandFailedError


class AndroidDeviceUtilsError(DcommError):
    pass  # General error class for device utils


class LocalFileNotFound(AndroidDeviceUtilsError):
    pass


class RemoteFileNotFound(AndroidDeviceUtilsError):
    pass


class WrongPermissions(AndroidDeviceUtilsError):
    pass


class FileAlreadyExists(AndroidDeviceUtilsError):
    pass


class OperationUnsupported(AndroidDeviceUtilsError):
    pass


class AndroidDeviceUtils:
    """
    Class exposing basic operations on an android device.
    Methods here control the device itself and not a specific app.
    Some methods may have to be overriden for a specific model,
    mainly due to differences in return values of adb commands
    """

    def __init__(self, connection):
        """
        :type connection: InternalAdbConnection
        """
        self.connection = connection

    def push(self, local_path, path_on_device):
        """
        Push a file/dir to the device.
        :type local_path: str
        :type path_on_device: str
        :rtype bool
        :raises LocalFileNotFound
        :raises RemoteFileNotFound
        :raises WrongPermissions
        :raises AdbConnectionError
        :raises AndroidDeviceUtilsError
        """
        try:
            output = self.connection.adb(["push", local_path, path_on_device])
        except CommandFailedError as err:
            if 'Read-only file system' in err.stderr:
                raise WrongPermissions()
            if 'No such file or directory' in err.stderr:
                raise LocalFileNotFound()
            if 'Is a directory' in err.stderr:
                raise RemoteFileNotFound()
            raise

        if not re.search(r'files? pushed', output, re.M):
            raise AndroidDeviceUtilsError('Unknown problem occurred')

    def pull(self, path_on_device, local_path):
        """
        Pull a file/dir to the device.
        :type path_on_device: str
        :type local_path: str
        :rtype: bool
        :raises LocalFileNotFound
        :raises RemoteFileNotFound
        :raises WrongPermissions
        :raises AdbConnectionError
        :raises AndroidDeviceUtilsError
        """
        try:
            output = self.connection.adb(["pull", path_on_device, local_path])
        except CommandFailedError as err:
            if 'Permission denied' in err.stderr:
                raise WrongPermissions()
            if 'No such file or directory' in err.stderr:
                raise RemoteFileNotFound()
            if 'Is a directory' in err.stderr:
                raise LocalFileNotFound()
            raise

        if not re.search(r'files? pulled', output, re.M):
            raise AndroidDeviceUtilsError('Unknown problem occurred')

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
        return self._shell("am", "broadcast", "-a", name, params_list)[0]

    def _shell(self, *args):
        """
        :type args: tuple(str)
        """
        # log.info("_shell params:", *args)
        return self.connection.adb(["shell"] + list(args))

    def mkdir(self, path_on_device):
        """
        Create a folder on the device
        :type path_on_device: str
        :raises FileAlreadyExists
        :raises WrongPermissions
        """
        try:
            output = self._shell("mkdir", path_on_device)
        except CommandFailedError as err:
            if 'No such file or directory' in err.stderr:
                raise RemoteFileNotFound()
            if 'File exists' in err.stderr:
                raise FileAlreadyExists()
            if 'Read-only file system' in err.stderr:
                raise WrongPermissions()
            raise

        if output.strip() != '':
            raise AndroidDeviceUtilsError('Unknown problem occurred')

    def rmdir(self, path_on_device):
        """
        Remove a folder and its contents on the device. A file will be removed as well.
        :type path_on_device: str
        :raises WrongPermissions
        """
        try:
            output = self._shell("rm", "-rf", path_on_device)
        except CommandFailedError as err:
            if 'Read-only file system' in err.stderr or 'No such file or directory' in err.stderr:
                # Trying to remove a read-only file resulted in 'No such file or directory', so not sure how to distinguish these two.
                raise WrongPermissions()
            raise

        if output.strip() != '':
            raise AndroidDeviceUtilsError('Unknown problem occurred')

    def touch_file(self, path_on_device):
        """
        touch a file on the device
        :type path_on_device: str
        """
        try:
            output = self._shell("touch", path_on_device)
        except CommandFailedError as err:
            if 'No such file or directory' in err.stderr:
                raise RemoteFileNotFound()
            if 'Read-only file system' in err.stderr:
                raise WrongPermissions()
            raise

        if output.strip() != '':
            raise AndroidDeviceUtilsError('Unknown problem occurred')

    def remove(self, path_on_device):
        """
        Remove a file on the device.
        :type path_on_device: str
        :raises WrongPermissions
        """
        try:
            output = self._shell("rm", "-f", path_on_device)
        except CommandFailedError as err:
            if 'Read-only file system' in err.stderr or 'No such file or directory' in err.stderr:
                # Trying to remove a read-only file resulted in 'No such file or directory', so not sure how to distinguish these two.
                raise WrongPermissions()
            raise

        if output.strip() != '':
            raise AndroidDeviceUtilsError('Unknown problem occurred')

    def ls(self, path_on_device):
        """
        According to ls -lat output: drwxrwx---   9 system cache     4096 2018-05-16 03:00 cache
        For files with permissions error, ret['permissions'] (and all other fields except name) will be None.
        MIGHT BE DEVICE SPECIFIC (UNLIKELY)
        :type path_on_device: str
        :rtype list[dict[permissions, n_links, owner, group, size, modified, name, links_to]]
        """
        try:
            output = self._shell("ls", "-lat", path_on_device)
            error = ''
        except CommandFailedError as err:
            # Make sure that all errors are just permission errors
            if any(['Permission denied' not in x for x in err.stderr.splitlines() if x.strip()]):
                if 'No such file or directory' in err.stderr:
                    raise RemoteFileNotFound()
                raise
            output = err.stdout
            error = err.stderr
        regular = re.findall('^(\S{10})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+\s+\S+)\s+([^>\n]+)$', output, re.M)
        links = re.findall('^(\S{10})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+\s+\S+)\s+(\S+) -> (\S+)$', output, re.M)
        no_perm = re.findall('\/([^\/\n]+): Permission denied', error, re.M)

        def get_dict(permissions=None, n_links=None, owner=None, group=None, size=None, modified=None, name=None,
                     links_to=None):
            n_links = int(n_links) if n_links is not None else None
            size = int(size) if size is not None else None
            modified = datetime.datetime.strptime(modified, '%Y-%m-%d %H:%M') if modified is not None else None
            return locals()

        ret = []
        for x in regular:
            ret.append(get_dict(*x))
        for x in links:
            ret.append(get_dict(*x))
        for x in no_perm:
            ret.append(get_dict(name=x))
        return ret

    @staticmethod
    def _local_file_exists(path):
        return '1' in subprocess.check_output('test -e {} && echo 1 || echo 0'.format(path), shell=True)

    def _remote_file_exists(self, path):
        return '1' in self.connection.adb(['shell', '[ -f {} ] && echo 1 || echo 0'.format(path)], timeout=1)

    def get_time(self):
        """
        :rtype: datetime
        """
        line = self._shell('date', '+"%Y-%m-%d\\', '%H:%M:%S:%N"').strip()
        return self._parse_time(line)

    def _parse_time(self, line):
        """
        helper for parse_time since oppo seems to work a bit differently from experia
        :param line:
        :return:
        """
        return datetime.datetime.strptime(line[:-3], '%Y-%m-%d\\ %H:%M:%S:%f')

    def get_device_name(self):
        """
        return the BUGATONE device name (used in recording scripts)
        :rtype: str
        """
        try:
            return self._shell("cat", "/data/local/tmp/devicename")
        except CommandFailedError as err:
            if 'No such file or directory' in err.stderr:
                raise OperationUnsupported()
            raise

    def get_prop(self, prop_name):
        """
        get a value of device property
        :type prop_name: str
        :rtype: str
        """
        return self._shell("getprop", prop_name).rstrip('\n')

    def set_prop(self, prop_name, value):
        """
        set a value of a device property.
        this method has no return value, so we return nothing
        :type prop_name: str
        :type value: str
        """
        self._shell("setprop", prop_name, '"' + value + '"')

    def reboot(self):
        """
        reboot the device
        """
        self.connection.adb("reboot", timeout=30)

    def _parse_dumpsys_volume(self):
        dumpsys_output = self._shell('dumpsys', 'audio')
        fields = re.findall(
            '- STREAM_MUSIC[^-]*Muted: (\w+)[^-]*Min: (\d+)[^-]*Max: (\d+)[^-]*Current: ([^\n]+)[^-]*Devices: ([^\n]+)\n',
            dumpsys_output)
        if not fields:
            raise AndroidDeviceUtilsError("Couldn't parse dumpsys")
        fields = fields[0]
        return dict(
            muted=fields[0].lower() == "true",
            min=int(fields[1]),
            max=int(fields[2]),
            current=map(lambda x: dict(
                id=x[0],
                name=x[1],
                vol=int(x[2]),
            ), re.findall('(\d+) \(([^)]+)\):\s*(\d+),?\s*', fields[3])),
            devices=fields[4].split(),
            device=fields[4].split()[0]
        )

    def _check_device_volume(self, dumpsys_output):
        """
        parse the dumpsys audio and check for device stream volume
        QUITE POSSIBLY DEVICE SPECIFIC
        :type dumpsys_output: str
        :rtype: int
        """
        device = re.findall(r'STREAM_MUSIC.*?Devices: (\w+)', dumpsys_output, re.DOTALL)[0]
        return int(re.findall(r'- STREAM_MUSIC.*?{}\): (\d+)'.format(device), dumpsys_output, re.DOTALL)[0])

    def is_earphone_connected(self):
        """
        :rtype: bool
        """
        return 'headset' == self._parse_dumpsys_volume()['device'].lower()

    def get_volume(self):
        """
        :rtype: int
        """
        fields = self._parse_dumpsys_volume()
        device = fields['device']
        try:
            return [x for x in fields['current'] if x['name'] == device][0]['vol']
        except Exception:
            raise AndroidDeviceUtilsError("Can't get headphone volume, you probably need to connect a headphone first.")

    def set_volume(self, val):
        """
        set the stream volume on the device
        :type val: int
        """
        max_vol = self.get_max_volume()
        if val > max_vol:
            raise ValueError("Can't set volume to {} because the maximum is {}".format(val, max_vol))
        self._shell("service", "call", "audio", "3", "i32", "3", "i32", str(val), "i32", "0")
        if val != self.get_volume():
            raise AndroidDeviceUtilsError("Could not set volume")

    def is_max_volume(self):
        """
        :rtype: bool
        """
        return self.get_volume() == self.get_max_volume()

    def get_max_volume(self):
        """
        get the max volume supported on the device
        :rtype: int
        """
        return self._parse_dumpsys_volume()['max']
