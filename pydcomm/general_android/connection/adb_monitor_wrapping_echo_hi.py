from pydcomm.general_android.connection.iadb_monitor import IAdbMonitor
from pydcomm.general_android.connection.wired_adb_connection import ConnectionClosedError


class AdbMonitorWrappingEchoHi(IAdbMonitor):
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        if not self._test_connection():
            raise ConnectionClosedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def is_connection_error(self):
        return not self._test_connection()

    def _test_connection(self):
        return self.connection.adb(["shell", "echo hi"], timeout=1, disable_fixers=True).strip() == "hi"
