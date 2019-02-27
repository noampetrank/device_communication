from pydcomm.general_android.connection.iadb_monitor import IAdbMonitor
from pydcomm.general_android.connection.internal_adb_connection import ConnectionClosedError


class AdbMonitorWrappingEchoHi(IAdbMonitor):
    def __init__(self, connection):
        """
        :param InternalAdbConnection connection:
        """
        self.connection = connection

    def __enter__(self):
        if not self.connection.test_connection():
            raise ConnectionClosedError()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.connection.test_connection():
            raise ConnectionClosedError()

    def is_connection_error(self):
        return not self.connection.test_connection()


class NullMonitor(IAdbMonitor):
    def __init__(self, _):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
