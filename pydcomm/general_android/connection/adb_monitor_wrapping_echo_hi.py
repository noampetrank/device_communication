from pydcomm.general_android.connection.iadb_monitor import IAdbMonitor
from pydcomm.general_android.connection.internal_adb_connection import ConnectionClosedError


class AdbMonitorWrappingEchoHi(IAdbMonitor):
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        if not self._test_connection():
            raise ConnectionClosedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._test_connection():
            raise ConnectionClosedError()

    def is_connection_error(self):
        return not self._test_connection()

    def _test_connection(self):
        try:
            return self.connection._run_adb_command(["-s", self.connection.device_id, "shell", "echo hi"],
                                                    timeout=1).strip() == "hi"
        except:
            return False


class EmptyMonitor(IAdbMonitor):
    def __init__(self, _):
        pass
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
