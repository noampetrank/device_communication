from pydcomm.general_android.android_device_utils import AndroidDeviceUtils
from pydcomm.public.iconnection import IConnection
from pydcomm.general_android.connection.wired_adb_connection import InternalAdbConnection, AdbConnectionError
from pybuga.infra.phone.adb_utils import LogCat


class AdbConnection(IConnection):
    def __init__(self, adb_connection):
        """

        :type adb_connection: InternalAdbConnection
        """
        self.adb_connection = adb_connection
        self.device_utils = AndroidDeviceUtils(self.adb_connection)

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
        self.device_utils.pull(path_on_device, local_path)

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
        self.device_utils.push(local_path, path_on_device)

    def shell(self, command, timeout_ms=None):
        """Run command on the device, returning the output.

        :param str command: Shell command to run.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :return: Output of command.
        :rtype: str
        """
        return self.adb_connection.adb(["shell", command], timeout=timeout_ms)

    def streaming_shell(self, command, timeout_ms=None):
        """
        Calls the shell command and returns an iterator of line from the stdout.
        The return object must have a method to stop the stream.
        TODO: Define this "stoppable" iterator thing.

        :param str command: Command to run.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :return: Stoppable iterator of lines from output.
        """
        # TODO: implement
        raise NotImplementedError

    def logcat(self, timeout_ms=None):
        """
        Stream of lines from logcat. Needs to be "stoppable".
        TODO: Define return object; maybe allow more parameters, e.g. -d.
        :param int|None timeout_ms: Maximum time to allow the command to run.
        :return: Stoppable iterator of lines from log.
        """

        # TODO: Make sure this is what's actually required
        cat = LogCat()
        cat.start()
        return cat

    def reboot(self):
        """Reboot the device"""
        self.device_utils.reboot()

    def root(self):
        """Restart adbd as root on the device.

        :return: Stdout of running command.
        :rtype: str
        """
        return self.adb_connection.adb("root")

    def remount(self):
        """Remount / as read-write."""
        self.adb_connection.adb("remount")

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
        cmd = ["install"]
        if replace_existing:
            cmd.append("-r")
        # TODO: grant_permissions
        cmd.append(apk_path)
        return self.adb_connection.adb(cmd, timeout=timeout_ms)

    def uninstall(self, package_name, keep_data=False, timeout_ms=None):
        """Removes a package from the device.

        :param str package_name: Package name of target package.
        :param bool keep_data: whether to keep the data and cache directories
        :param int|None timeout_ms: Expected timeout for pushing and installing.
        :return The uninstall output.
        """
        cmd = ["uninstall"]
        if keep_data:
            cmd.append("-k")
        cmd.append(package_name)
        return self.adb_connection.adb(cmd, timeout=timeout_ms)

    def device_id(self):
        """Return serial number of connected device.

        :rtype: str
        """
        return self.shell("cat /data/local/tmp/devicename")

    def disconnect(self):
        """Closes connection."""
        self.adb_connection.disconnect()
