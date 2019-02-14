"""
Connection interfaces, factories and default user interface

This file defines the Connection interface: what functions must exist for basic connections, with their argument
names, types, and return type. A main theme is the lack of mention of "adb", and instead the names of all the
different functionalities of adb appear.

This files includes the definitions and imports of all existing connection factories. Factories that aren't defined
in this file are imported, and all factories are added to the global dictionary at the bottom section.

Lastly this file
"""


from pydcomm import DcommError
from pydcomm.public.ux_stats import metacollectstats


class ConnectionError(DcommError):
    """Error that happens during the connection process"""
    pass


class ConnectionClosedError(DcommError):
    pass


class IConnection(object):
    """Interface for connections.

    Generally speaking, this wraps (almost) all functionality of google's adb, without mentioning adb.
    Since it wraps (almost) all functionality, this interface is comprehensive enough for all hardcore users of device
    communications, and any code that previously needed adb.
    Since it doesn't mention adb by name, the actual implementation can be different (there are alternatives to adb
    out there), benchmarks don't know about adb, and everyone can be happy.
    """
    __metaclass__ = metacollectstats

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

    def streaming_shell(self, command, timeout_ms=None):
        """
        Calls the shell command and returns an iterator of line from the stdout.
        The return object must have a method to stop the stream.
        TODO: Define this "stoppable" iterator thing.

        :param str command: Command to run.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :return: Stoppable iterator of lines from output.
        """
        raise NotImplementedError

    def logcat(self, timeout_ms=None, dump=True, clear=False):
        """
        Stream of lines from logcat. Needs to be "stoppable".
        TODO: Define return object; maybe allow more parameters, e.g. -d.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :param bool dump: Whether to dump the current logs (logcat -d)
        :param bool clear: Whether to clear all logcat (logcat -c). Returns nothing
        :return: Stoppable iterator of lines from log.
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

    def device_id(self):
        """Return serial number of connected device.

        :rtype: str
        """
        raise NotImplementedError

    def disconnect(self):
        """Closes connection."""
        raise NotImplementedError


class ConnectionFactory(object):
    """Interface for factories creating connections."""
    __metaclass__ = metacollectstats

    @classmethod
    def create_connection(cls, device_id=None, **kwargs):
        """Create connection

        :param str|None device_id: Specific device id to connect to. If none given, must call `choose_device_id()`.
        :param kwargs:
        :rtype: IConnection
        """
        raise NotImplementedError

    @classmethod
    def connected_devices(cls):
        """Returns list of serial numbers of connected devices.

        :rtype: list[str]
        """
        raise NotImplementedError

    @classmethod
    def choose_device_id(cls):
        """
        This opens a user interface for choosing possible device for this factory.
        :return: String representing device id, that can be passed to `wired_connection` and to `wireless_conenction`.
        :type: str
        """
        raise NotImplementedError
