########################################################################################################################
#   Dummy connections
#
# This section is for a fixed dummy implementation of connection.
from pydcomm.public.bugarpc import IRemoteProcedureCaller, ICallerFactory
from pydcomm.public.iconnection import IConnection, ConnectionClosedError, ConnectionFactory


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

    def device_id(self):
        if not self._connected:
            raise ConnectionClosedError

        return "dummybugadevice01"


class DummyConnectionFactory(ConnectionFactory):
    @classmethod
    def choose_device_id(cls):
        return "dummybugadevice01"

    @classmethod
    def connected_devices(cls):
        return ["dummybugadevice01"]

    @classmethod
    def create_connection(cls, device_id=None, **kwargs):
        return DummyConnection()


class DummyRemoteProcedureCaller(IRemoteProcedureCaller):
    def call(self, procedure_name, params):
        import numpy as np
        if procedure_name == "_rpc_get_version":
            return "1.0"
        elif procedure_name == "dummy_send":
            return (np.frombuffer(params, np.uint8) + 1).tostring()
        elif procedure_name == "_rpc_stop":
            return "stopped"
        else:
            raise ValueError("No such procedure name: {}".format(procedure_name))

    def get_version(self):
        return "1.0"


class DummyCallerFactory(ICallerFactory):
    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        assert device_id is None or device_id == "dummy", "Dummy device must have id dummy"
        return DummyRemoteProcedureCaller()

    @classmethod
    def install(cls, so_path, device_id=None):
        assert device_id is None or device_id == "dummy", "Dummy device must have id dummy"

    @classmethod
    def choose_device_id(cls):
        return "dummy"
