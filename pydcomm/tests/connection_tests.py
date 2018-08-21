import time
from unittest import TestCase

"""
TODO:
# Benchmark table
#   Wired
#       No recovery
#       With recovery
#   Wireless
#       No recovery - from ip
#       No recovery - from device
#       With recovery - from ip
#       With recovery - from device
#   
#   Long run
#   Many short connections
#   Adb shell multiple times
Mock tests
  Failing tests
Real tests
  Stress tests
"""


class ConnectionBencmark(TestCase):

    def _test_connection_is_working(self, connection):
        return connection.adb("shell echo hi") == "hi"

    def _test_connection_and_disconnect(self, connection):
        if not self._test_connection_is_working(connection):
            connection.disconnect()
            return False
        connection.disconnect()
        if self._test_connection_is_working(connection):
            raise Exception("Could not disconnect")

    def repeat_test_connection(self, connect_from_ip, recovery, rounds, sleep_between_connections):
        connection_factory = ConnectionFactory()
        # User intervention
        connection = connection_factory.get_connected(auto_recovery=recovery)
        ip = connection.get_connection_status()["ip"]
        connection.disconnect()
        fail = 0
        for i in range(rounds):
            if connect_from_ip:
                connection = Connection(ip)
            else:
                connection = connection_factory.get_connected(auto_recovery=recovery)
            fail += self._test_connection_and_disconnect(connection)
            time.sleep(sleep_between_connections)
        return fail, rounds


class ConnectionUnitTests(TestCase):
    pass
