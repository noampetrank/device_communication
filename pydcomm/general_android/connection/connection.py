"""
Connection interfaces classes

These interfaces are meant to be almost permanent.
The interfaces have absolutely no implementation.
Every function has names for arguments, types for arguments, and return type, which are fixed for all implemenations.

"""


from pydcomm import DcommError


class ConnectionError(DcommError):
    """Error that happens during the connection process"""
    pass


class ConnectionClosedError(DcommError):
    pass


class Connection(object):
    """Interface for connections.

    Generally speaking, this wraps (almost) all functionality of google's adb, without mentioning adb.
    Since it wraps (almost) all functionality, this interface is comprehensive enough for all hardcore users of device
    communications, and any code that previously needed adb.
    Since it doesn't mention adb by name, the actual implementation can be different (there are alternatives to adb
    out there), benchmarks don't know about adb, and everyone can be happy.
    """
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
        raise NotImplementedError

    def push(self, local_path, path_on_device):
        """
        Push a file/dir to the device.
        :type local_path: str
        :type path_on_device: str
        :rtype: bool
        :raises LocalFileNotFound
        :raises RemoteFileNotFound
        :raises WrongPermissions
        :raises AdbConnectionError
        :raises AndroidDeviceUtilsError
        """
        raise NotImplementedError

    def shell(self, command, timeout_ms=None):
        """Run command on the device, returning the output.

        :param str command: Shell command to run.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :return: Output of command.
        :rtype: str
        """
        raise NotImplementedError

    def reboot(self):
        """Reboot the device"""
        raise NotImplementedError

    def root(self):
        """Restart adbd as root on the device.

        :return: Stdout of running command.
        :rtype: str
        """
        raise NotImplementedError

    def remount(self):
        """Remount / as read-write."""
        raise NotImplementedError

    def install(self, apk_path, destination_dir='/system/app/',
                replace_existing=True, grant_permissions=False, timeout_ms=None):
        """Install an apk to the device.

        :param str apk_path: Local path to apk to install.
        :param str destination_dir: Optional destination directory. Use /system/app/ for persistent applications.
        :param bool replace_existing: whether to replace existing application
        :param bool grant_permissions: If True, grant all permissions to the app specified in its manifest
        :param int|None timeout_ms: Expected timeout for pushing and installing.
        :return The install output.
        """
        raise NotImplementedError

    def uninstall(self, package_name, keep_data=False, timeout_ms=None):
        """Removes a package from the device.

        :param str package_name: Package name of target package.
        :param bool keep_data: whether to keep the data and cache directories
        :param int|None timeout_ms: Expected timeout for pushing and installing.
        :return The uninstall output.
        """
        raise NotImplementedError

    def serial_number(self):
        """Return serial number of connected device.

        :rtype: str
        """
        raise NotImplementedError

    def disconnect(self):
        """Closes connection."""
        raise NotImplementedError

    @classmethod
    def connected_devices_serials(cls):
        """Returns list of serial numbers of connected devices.

        :rtype: list[str]
        """
        raise NotImplementedError

    def test_connection(self):
        """Tests and returns if the connection is still available.

        :rtype: bool
        """
        raise NotImplementedError


# noinspection PyAbstractClass
class BugaConnection(Connection):
    """Like a Connection, but with added Buga things that we just must have.

    """
    def device_name(self):
        """Returns device name given by Bugatone

        :rtype: str
        :raises: NameError
        """
        raise NotImplementedError

    @classmethod
    def connected_devices_names(cls):
        """Returns list of names of connected devices.

        :rtype: list[str]
        """
        raise NotImplementedError


class ConnectionFactory(object):
    """Interface for factories creating connections."""
    @classmethod
    def wired_connection(cls, **kwargs):
        """Get wired connection

        :param kwargs:
        :rtype: Connection
        """
        raise NotImplementedError


class BugaConnectionFactory(ConnectionFactory):
    """Interface for factories creating buga connections."""
    @classmethod
    def wired_connection(cls, **kwargs):
        """Get wired buga connection

        :param kwargs:
        :rtype: BugaConnection
        """
        raise NotImplementedError

########################################################################################################################


class DummyBugaConnection(BugaConnection):
    def __init__(self):
        self._pushed = {}
        self._connected = True

    def test_connection(self):
        return self._connected

    def disconnect(self):
        if not self._connected:
            raise ConnectionClosedError

        self._connected = False

    @classmethod
    def connected_devices_names(cls):
        return ["DummyBugaDevice"]

    @classmethod
    def connected_devices_serials(cls):
        return ["dummybugadevice01"]

    def device_name(self):
        return "DummyBugaDevice"

    def pull(self, path_on_device, local_path):
        if not self._connected:
            raise ConnectionClosedError

        import os
        path_on_device = os.path.abspath(os.path.join("/", path_on_device))
        open(local_path, "wb").write(self._pushed[path_on_device])

        return True

    def push(self, local_path, path_on_device):
        if not self._connected:
            raise ConnectionClosedError

        import os
        path_on_device = os.path.abspath(os.path.join("/", path_on_device))
        self._pushed[path_on_device] = open(local_path, "rb").read()

        return True

    def shell(self, command, timeout_ms=None):
        if not self._connected:
            raise ConnectionClosedError

        if command.startswith("rm "):
            self._pushed.pop(command[3:], None)
            return ""
        elif command.startswith("echo "):
            import subprocess32
            return subprocess32.check_output(command, shell=True).strip()

        raise TypeError

    def reboot(self):
        if not self._connected:
            raise ConnectionClosedError

        return ""

    def root(self):
        if not self._connected:
            raise ConnectionClosedError

        return ""

    def remount(self):
        if not self._connected:
            raise ConnectionClosedError

        return ""

    def install(self, apk_path, destination_dir='/system/app/', replace_existing=True, grant_permissions=False,
                timeout_ms=None):
        if not self._connected:
            raise ConnectionClosedError

        return ""

    def uninstall(self, package_name, keep_data=False, timeout_ms=None):
        if not self._connected:
            raise ConnectionClosedError

        return ""

    def serial_number(self):
        if not self._connected:
            raise ConnectionClosedError

        return "dummybugadevice01"


class DummyBugaConnectionFactory(BugaConnectionFactory):
    @classmethod
    def wired_connection(cls, **kwargs):
        return DummyBugaConnection()
