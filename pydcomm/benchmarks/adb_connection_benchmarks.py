import json
import time
import tqdm
from collections import defaultdict

from enum import IntEnum
from pydcomm.general_android.connection.wired_adb_connection import AdbConnectionError

from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
from pydcomm.general_android.connection.connection_fixers import add_rooted_impl, set_usb_mode_to_mtp_fix, restart_adb_server_fix
from pydcomm.general_android.connection.fixers.connected_usb_device_fixes import forgot_device_fix, device_turned_off
from pydcomm.general_android.connection.decorator_helpers import add_adb_recovery_decorator, add_init_decorator

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

    return add_adb_recovery_decorator(f, "counter for " + name)


class ConnectionBenchmark(object):
    @staticmethod
    def test_connection(connection, test_disconnection=False):
        try:
            return connection.adb("shell echo hi", disable_fixers=test_disconnection) == "hi"
        except AdbConnectionError:
            if not test_disconnection:
                raise
            return False

    def repeat_test_connection(self, rooted, connect_from_ip, recovery, rounds, sleep_between_connections, connection_test_amount,
                               connection_length, verbose=True):
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
        connection = AdbConnectionFactory.get_oppo_wireless_device()

        ip = connection.device_id
        connection.disconnect()
        time.sleep(0.5)
        fails = defaultdict(lambda: 0)
        for _ in tqdm.tqdm(range(rounds), disable=not verbose, desc="Connection rounds:", unit="connection"):
            connection = AdbConnectionFactory.get_oppo_wireless_device()
            for j in range(connection_test_amount):
                if not self.test_connection(connection):
                    fails["shell"] += 1
                time.sleep(connection_test_amount / connection_length)
            connection.disconnect()
            if self.test_connection(connection, test_disconnection=True):
                fails["disconnect"] += 1
            for k in self.fail_dict:
                fails[k] += self.fail_dict[k]
            time.sleep(sleep_between_connections)
        return fails, rounds


def main():
    rooted = False
    bench = ConnectionBenchmark()
    results = {}
    recovery_type = Recovery.AUTO
    try:
        results["10x1x0"] = bench.repeat_test_connection(
            rooted=rooted,  # Unused for now
            connect_from_ip=False,  # Unused for now
            recovery=recovery_type,
            rounds=1000,
            sleep_between_connections=0,
            connection_test_amount=1,
            connection_length=10)
        print_results(results)
    except Exception as e:
        print(e)
    try:
        results["180x18x0"] = bench.repeat_test_connection(
            rooted=rooted,
            connect_from_ip=True,
            recovery=recovery_type,
            rounds=100,
            sleep_between_connections=0,
            connection_length=180,
            connection_test_amount=18)
        print_results(results)
    except Exception as e:
        print(e)
    try:
        results["180x1x0"] = bench.repeat_test_connection(
            rooted=rooted,
            connect_from_ip=True,
            recovery=recovery_type,
            rounds=100,
            sleep_between_connections=0,
            connection_length=180,
            connection_test_amount=18)
        print_results(results)
    except Exception as e:
        print(e)
    try:
        results["10x2x120"] = bench.repeat_test_connection(
            rooted=rooted,
            connect_from_ip=True,
            recovery=recovery_type,
            rounds=100,
            sleep_between_connections=120,
            connection_length=10,
            connection_test_amount=2)
        print_results(results)
    except Exception as e:
        print(e)
    print(results)


def print_results(res):
    print("\n\n")
    print(json.dumps(dict(res), indent=4, sort_keys=True))


"""
                   total_cons con_fail auto_rec_fail manu_rec_fail total_fail
TestName                                                                     
10x1x0xfrom ip           1000      100            80            20          0
180x18x0xfrom ip          100       10             9             1          0
180x1x0xfrom ip           100       10            10             0          0
10x2x120xfrom ip          100        2             2             0          0

Testname - length of connection X how many times to test per connection x sleep between connections x connect from ip or manually
"""

if __name__ == "__main__":
    main()
