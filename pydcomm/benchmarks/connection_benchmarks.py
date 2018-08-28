# TODO: Everything is terrible. We must implement how the fixing mechanism works and build the tracing into it.
from collections import defaultdict

from enum import IntEnum
import time

from pydcomm.connection import Connection, ConnectionFactory, add_automated_recovery, add_interactive_troubleshooting_recovery

"""
Sample Benchmark:
Device:                      Oppo Find X
Connection (Wired|Wireless): Wireless
Short connections:
    Total: 100
    Successful:90
    Auto recover: 8
    Manual recover: 2
    Fail: 0
Long connection, echo command every 10s:
    Success: 100/100
    Average connection duration: 60m
    Total: 100
    Successful:90
    Auto recover: 8
    Manual recover: 2
    Fail: 0
Long connection, echo command every 120s: 100/100
    Success: 100/100
    Average connection duration: 60m
    Total: 100
    Successful:90
    Auto recover: 8
    Manual recover: 2
    Fail: 0
Simulate disconnect device (wired, wireless):
    Total: 100
    Recovery: 100
    Failed: 0
* All numbers are not final

"""


class Recovery(IntEnum):
    NONE = 0
    AUTO = 1
    INTERACTIVE = 2


def create_log_fix(dict, name):
    def f(connection):
        dict[name] += 1

    return f


class ConnectionBenchmark(object):
    # Not good, need to find a better solution
    def _create_connection(self, recovery, ip=None):
        self.fail_dict = defaultdict()
        con = Connection(ip)
        con.fixes.append(create_log_fix(self.fail_dict, "first_fail"))
        if recovery > Recovery.AUTO:
            con = add_automated_recovery(con)
        con.fixes.append(create_log_fix(self.fail_dict, "auto_fail"))
        if recovery > Recovery.INTERACTIVE:
            con = add_interactive_troubleshooting_recovery(con)
        con.fixes.append(create_log_fix(self.fail_dict, "complete_fail"))
        return con

    @staticmethod
    def _test_connection_is_working(connection):
        return connection.adb("shell echo hi") == "hi"

    def _test_connection_and_disconnect(self, connection, connection_test_amount, sleep_between_connection_test):
        for i in range(connection_test_amount):
            if not self._test_connection_is_working(connection):
                connection.disconnect()
                return False
            time.sleep(sleep_between_connection_test)
        connection.disconnect()
        if self._test_connection_is_working(connection):
            raise Exception("Could not disconnect")

    def repeat_test_connection(self, rooted, connect_from_ip, recovery, rounds, sleep_between_connections, connection_test_amount, sleep_between_connection_test):
        """
        Returns dictionary containing in which part of the recovery it failed and number of rounds.
        :param rooted:
        :param connect_from_ip:
        :param recovery:
        :param rounds:
        :param sleep_between_connections:
        :param connection_test_amount:
        :param sleep_between_connection_test:
        :return:
        """
        connection = self._create_connection(recovery, False)

        ip = connection.get_connection_status()["ip"]
        connection.disconnect()
        fails = defaultdict()
        for i in range(rounds):
            connection = self._create_connection(recovery, ip if connect_from_ip else None)
            self._test_connection_and_disconnect(connection, connection_test_amount, sleep_between_connection_test)
            for k in self.fail_dict:
                fails[k]+=self.fail_dict[k]
            time.sleep(sleep_between_connections)
        return fails, rounds


def main():
    rooted = True
    banch = ConnectionBenchmark()
    results = {}
    results["short_connections"] = banch.repeat_test_connection(rooted=rooted,
                                                                connect_from_ip=True,
                                                                ecovery=Recovery.INTERACTIVE,
                                                                rounds=1000,
                                                                sleep_between_connections=0,
                                                                connection_length=0)
    results["long_connections"] = banch.repeat_test_connection(rooted=rooted,
                                                               connect_from_ip=True,
                                                               ecovery=Recovery.INTERACTIVE,
                                                               rounds=100,
                                                               sleep_between_connections=30,
                                                               connection_length=30)
    pass
