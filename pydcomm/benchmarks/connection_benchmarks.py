import time
from collections import defaultdict

from enum import IntEnum

from pydcomm.connection import ConnectionFactory
from pydcomm.connection_decorators import auto_fixes, add_some_recovery, manual_fixes, add_rooted_impl

"""
                   total_cons con_fail auto_rec_fail manu_rec_fail total_fail
TestName                                                                     
10x1x0xfrom ip           1000      100            80            20          0
180x18x0xfrom ip          100       10             9             1          0
180x1x0xfrom ip           100       10            10             0          0
10x2x120xfrom ip          100        2             2             0          0
10x2x0xfrom device         50        0             0             0          0

Testname - length of connection X how many times to test per connection x sleep between connections x connect from ip or manually
"""


class Recovery(IntEnum):
    NONE = 0
    AUTO = 1
    INTERACTIVE = 2


def create_log_fix(fail_dict, name):
    def f(connection):
        fail_dict[name] += 1

    return add_some_recovery(f)


class ConnectionBenchmark(object):
    # Not good, need to find a better solution
    def _create_connection(self, recovery, rooted, ip=None):
        self.fail_dict = defaultdict()
        cf = ConnectionFactory()
        decorators = []
        if rooted:
            decorators.append(add_rooted_impl)
        decorators.append(create_log_fix(self.fail_dict, "connection_fail"))
        if recovery >= Recovery.AUTO:
            decorators.append(add_some_recovery(auto_fixes))
            decorators.append(create_log_fix(self.fail_dict, "auto_recover_fail"))
        if recovery >= Recovery.INTERACTIVE:
            decorators.append(add_some_recovery(manual_fixes))
            decorators.append(create_log_fix(self.fail_dict, "manual_recover_fail"))
        con = cf.create_connection(ip=ip, decorators=decorators)
        return con

    @staticmethod
    def _test_connection_is_working(connection):
        return connection.adb(["shell", "echo", "hi"]) == "hi"

    def repeat_test_connection(self, rooted, connect_from_ip, recovery, rounds, sleep_between_connections, connection_test_amount,
                               connection_length):
        """
        Returns dictionary containing in which part of the recovery it failed and number of rounds.
        :param connection_length: How long the connection is open in seconds
        :param rooted: Should start a rooted connection
        :param connect_from_ip:
        :param recovery:
        :param rounds:
        :param sleep_between_connections:
        :param connection_test_amount:
        :return:
        """
        connection = self._create_connection(recovery, False)

        ip = connection.get_connection_status()["ip"]
        connection.disconnect()
        fails = defaultdict()
        for i in range(rounds):
            connection = self._create_connection(recovery, rooted, ip if connect_from_ip else None)
            for i in range(connection_test_amount):
                if not self._test_connection_is_working(connection):
                    fails["shell"] += 1
                time.sleep(connection_test_amount / connection_length)
            connection.disconnect()
            if self._test_connection_is_working(connection):
                fails["disconnect"] += 1
            for k in self.fail_dict:
                fails[k] += self.fail_dict[k]
            time.sleep(sleep_between_connections)
        return fails, rounds


def main():
    rooted = True
    bench = ConnectionBenchmark()
    results = {}
    results["short_connections"] = bench.repeat_test_connection(rooted=rooted,
                                                                connect_from_ip=True,
                                                                recovery=Recovery.INTERACTIVE,
                                                                rounds=1000,
                                                                sleep_between_connections=0,
                                                                connection_test_amount=1,
                                                                connection_length=10)
    results["long_connections"] = bench.repeat_test_connection(rooted=rooted,
                                                               connect_from_ip=True,
                                                               recovery=Recovery.INTERACTIVE,
                                                               rounds=100,
                                                               sleep_between_connections=0,
                                                               connection_length=180,
                                                               connection_test_amount=18)
    # TODO: Add rest of table tests
