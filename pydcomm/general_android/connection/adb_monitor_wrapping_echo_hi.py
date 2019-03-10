from pydcomm.general_android.connection.iadb_monitor import IAdbMonitor
from pydcomm.public.iconnection import ConnectionClosedError


class AdbMonitorWrappingEchoHi(IAdbMonitor):
    def __init__(self, connection):
        """
        :param InternalAdbConnection connection:
        """
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: uncomment after monitor is done in a more efficient way
        # if not self.connection.test_connection():
        #     raise ConnectionClosedError()
        pass

    def is_connection_error(self):
        return not self.connection.test_connection()


class NullMonitor(IAdbMonitor):
    def __init__(self, _):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def is_connection_error(self):
        return False
