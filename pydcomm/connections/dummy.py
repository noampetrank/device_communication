########################################################################################################################
#   Dummy connections
#
# This section is for a fixed dummy implementation of connection.
from pydcomm.general_android.connection import IConnection
from pydcomm.public.iconnection import ConnectionClosedError, ConnectionFactory


class DummyConnection(IConnection):
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

    @staticmethod
    def device_name():
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

    def logcat(self, timeout_ms=None):
        return ["bah"]

    def streaming_shell(self, command, timeout_ms=None):
        return [self.shell(command)]

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


class DummyConnectionFactory(ConnectionFactory):
    @classmethod
    def choose_device_id(cls):
        return "dummybugadevice01"

    @classmethod
    def connected_devices_serials(cls):
        return ["dummybugadevice01"]

    @classmethod
    def wireless_connection(cls, **kwargs):
        return DummyConnection()

    @classmethod
    def wired_connection(cls, **kwargs):
        return DummyConnection()
