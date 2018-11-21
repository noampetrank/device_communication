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
from pydcomm.utils.userexpstats import metacollectstats


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

    def test_connection(self):
        """Tests and returns if the connection is still available.

        :rtype: bool
        """
        raise NotImplementedError


# noinspection PyAbstractClass
class BugaConnection(Connection):
    """Like a Connection, but with added Buga things that we just must have.
    This is currently out of scope, to be done later.
    """
    def device_name(self):
        """Returns device name given by Bugatone
        This is currently out of scope, to be done later.

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
    __metaclass__ = metacollectstats

    @classmethod
    def wired_connection(cls, device_id=None, **kwargs):
        """Get wired connection

        :param str|None device_id: Specific device id to connect to. If none given, must call `choose_device_id()`.
        :param kwargs:
        :rtype: Connection
        """
        if device_id is None:
            return cls.wired_connection(device_id=cls.choose_device_id(), **kwargs)

        raise NotImplementedError

    @classmethod
    def wireless_connection(cls, device_id=None, **kwargs):
        """Get wireless connection

        :param str|None device_id: Specific device id to connect to. If none given, must call `choose_device_id()`.
        :param kwargs:
        :rtype: Connection
        """
        if device_id is None:
            return cls.wireless_connection(device_id=cls.choose_device_id(), **kwargs)

        raise NotImplementedError

    @classmethod
    def connected_devices_serials(cls):
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


class BugaConnectionFactory(ConnectionFactory):
    """Interface for factories creating buga connections."""

    @classmethod
    def choose_device_id(cls):
        pass

    @classmethod
    def connected_devices_serials(cls):
        raise NotImplementedError

    @classmethod
    def wireless_connection(cls, device_id=None, **kwargs):
        raise NotImplementedError

    @classmethod
    def wired_connection(cls, device_id=None, **kwargs):
        raise NotImplementedError

########################################################################################################################
#   Dummy connections
#
# This section is for a fixed dummy implementation of connection.

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


########################################################################################################################
#
# Connection Factories
#
# Add definitions and imports of connection factories in this section and add them to the global dictionary of
# connection factories. Choose a short, indicative key, one that will be easy to identify and type in a user menu.

all_connection_factories = {}

#
# Example:
#   class MyConnectionFactory(ConnectionFactory):
#       ...
#
#   all_connection_factories.append(MyConnectionFactory)
#


class DummyBugaConnectionFactory(BugaConnectionFactory):
    @classmethod
    def wireless_connection(cls, **kwargs):
        return DummyBugaConnection()

    @classmethod
    def wired_connection(cls, **kwargs):
        return DummyBugaConnection()


all_connection_factories['dummy'] = DummyBugaConnectionFactory
