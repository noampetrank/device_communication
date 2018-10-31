import json
import time
import tqdm
from collections import defaultdict

from enum import IntEnum

from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
from pydcomm.general_android.connection.connection_fixers import add_rooted_impl, set_usb_mode_to_mtp_fix, restart_adb_server_fix, add_no_device_connected_recovery
from pydcomm.general_android.connection.fixes.connected_usb_device_fixes import forgot_device_fix, device_turned_off
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
    # Not good, need to find a better solution
    def _create_connection(self, recovery, rooted, ip=None):
        self.fail_dict = defaultdict()
        cf = AdbConnectionFactory()
        # TODO: Move all of these into the ConnectionFactory.
        decorators = []
        if rooted:
            decorators.append(add_init_decorator(add_rooted_impl, "add_rooted_impl"))
        decorators.append(create_log_fix(self.fail_dict, "connection_fail"))
        if recovery >= Recovery.AUTO:
            decorators.append(add_adb_recovery_decorator(restart_adb_server_fix, "restart_adb_server_fix"))
            decorators.append(add_adb_recovery_decorator(set_usb_mode_to_mtp_fix, "set_usb_mode_to_mtp_fix"))
            decorators.append(create_log_fix(self.fail_dict, "auto_recover_fail"))
        if recovery >= Recovery.INTERACTIVE:
            decorators.append(add_no_device_connected_recovery)
            decorators.append(add_adb_recovery_decorator(set_usb_mode_to_mtp_fix, "set_usb_mode_to_mtp_fix"))
            decorators.append(add_adb_recovery_decorator(forgot_device_fix, "forgot_device_fix"))
            decorators.append(add_adb_recovery_decorator(device_turned_off, "device_turned_off"))
            decorators.append(create_log_fix(self.fail_dict, "manual_recover_fail"))
        con = cf.create_connection(wired=True, ip=ip, decorators=decorators)
        return con

    @staticmethod
    def test_connection(connection):
        return connection.adb("shell", "echo hi").strip() == "hi"

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
        connection = self._create_connection(recovery, rooted=False)

        ip = connection.device_id
        connection.disconnect()
        fails = defaultdict(lambda: 0)
        for _ in tqdm.tqdm(range(rounds), disable=not verbose, desc="Connection rounds:", unit="connection"):
            connection = self._create_connection(recovery, rooted, ip if connect_from_ip else None)
            for j in range(connection_test_amount):
                if not self.test_connection(connection):
                    fails["shell"] += 1
                time.sleep(connection_test_amount / connection_length)
            connection.disconnect()
            if self.test_connection(connection):
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
            connect_from_ip=True,  # Unused for now
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
