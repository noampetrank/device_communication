import __builtin__
import json
import time
from collections import defaultdict

import mock
import tqdm
from benchmarks.raw_input_recorder import RawInputRecorder
from enum import IntEnum
from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
from pydcomm.general_android.connection.decorator_helpers import add_adb_recovery_decorator
from pydcomm.general_android.connection.wired_adb_connection import AdbConnectionError

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

    return add_adb_recovery_decorator(f)


class ApiCallData(object):
    def __init__(self, type, total_time, success, manual_interactions_count, manual_times, failure_reason):
        self.type = type
        self.total_time = total_time
        self.success = success
        self.manual_interactions_count = manual_interactions_count
        self.manual_times = manual_times
        self.failure_reason = failure_reason


class ConnectionBenchmark(object):
    def __init__(self):
        self.stats = []     # type: list[ApiCallData]

    @mock.patch.object(__builtin__, 'raw_input')
    def benchmark_adb(self, connection, mock_raw_input):
        input_recorder = RawInputRecorder()
        mock_raw_input.side_effect = input_recorder

        success = False
        failure_reason = None
        start_time = time.time()

        try:
            success = connection.adb("shell echo hi") == "hi"
        except Exception as e:
            failure_reason = e.__class__.__name__
        finally:
            end_time = time.time()
            self.stats.append(ApiCallData("adb",                            # type
                                          end_time - start_time,            # time
                                          success,                          # success
                                          len(input_recorder.input_times),  # manual_interactions_count
                                          input_recorder.input_times,       # manual_times
                                          failure_reason))                  # failure_reason
            return success

    @mock.patch.object(__builtin__, 'raw_input')
    def benchmark_connect(self, mock_raw_input):
        input_recorder = RawInputRecorder()
        mock_raw_input.side_effect = input_recorder

        connection = None
        failure_reason = None
        start_time = time.time()

        try:
            connection = AdbConnectionFactory.get_oppo_wireless_device()
        except Exception as e:
            failure_reason = e.__class__.__name__
            raise
        finally:
            end_time = time.time()
            self.stats.append(ApiCallData("connect",                        # type
                                          end_time - start_time,            # time
                                          connection is not None,           # success
                                          len(input_recorder.input_times),  # manual_interactions_count
                                          input_recorder.input_times,       # manual_times
                                          failure_reason))                  # failure_reason
            return connection

    def benchmark_disconnect(self, connection):
        success = False
        failure_reason = None
        end_time = None
        start_time = time.time()

        try:
            connection.disconnect()
            end_time = time.time()

            # Expect that adb raises exception
            try:
                connection.adb("shell echo hi")
            except AdbConnectionError as e:
                if e.message == "This connection was closed":
                    success = True
                else:
                    raise
        except Exception as e:
            failure_reason = e.__class__.__name__
        finally:
            if end_time is None:
                end_time = time.time()
            self.stats.append(ApiCallData("disconnect",             # type
                                          end_time - start_time,    # time
                                          success,                  # success
                                          0,                        # manual_interactions_count
                                          [],                       # manual_times
                                          failure_reason))          # failure_reason
            return connection

    def run(self, num_connection_checks, check_interval):
        try:
            # Connect
            print("Connecting...")  # TODO: remove
            connection = self.benchmark_connect()

            # Check if connection is alive
            for i in range(num_connection_checks):
                print("adb...")  # TODO: remove
                self.benchmark_adb(connection)
                print("adb done")  # TODO: remove
                time.sleep(check_interval)

            # Disconnect
            print("Disconnecting...")  # TODO: remove
            self.benchmark_disconnect(connection)
            print("Disconnecting done")  # TODO: remove
        except Exception as e:
            print("Got exception. Aborting this run. Details: " + e.__class__.__name__ + ": " + e.message)

#     def repeat_test_connection(self, rooted, connect_from_ip, recovery, rounds, sleep_between_connections, connection_test_amount,
#                                connection_length, verbose=True):
#         """
#         Returns dictionary containing in which part of the recovery it failed and number of rounds.
#         :param connection_length: How long the connection is open in seconds
#         :param rooted: Should start a rooted connection
#         :param connect_from_ip:
#         :param recovery:
#         :param rounds:
#         :param sleep_between_connections:
#         :param connection_test_amount:
#         :return:
#         """
#         connection = AdbConnectionFactory.get_oppo_wireless_device()
#
#         ip = connection.device_id
#         connection.disconnect()
#         time.sleep(0.5)
#         fails = defaultdict(lambda: 0)
#         for _ in tqdm.tqdm(range(rounds), disable=not verbose, desc="Connection rounds:", unit="connection"):
#             connection = AdbConnectionFactory.get_oppo_wireless_device()
#             for j in range(connection_test_amount):
#                 if not self.test_connection_is_alive(connection):
#                     fails["shell"] += 1
#                 time.sleep(connection_test_amount / connection_length)
#             connection.disconnect()
#             if self.test_connection_is_alive(connection, test_disconnection=True):
#                 fails["disconnect"] += 1
#             for k in self.fail_dict:
#                 fails[k] += self.fail_dict[k]
#             time.sleep(sleep_between_connections)
#         return fails, rounds
#
#
# def main():
#     rooted = False
#     bench = ConnectionBenchmark()
#     results = {}
#     recovery_type = Recovery.AUTO
#     try:
#         results["10x1x0"] = bench.repeat_test_connection(
#             rooted=rooted,  # Unused for now
#             connect_from_ip=False,  # Unused for now
#             recovery=recovery_type,
#             rounds=1000,
#             sleep_between_connections=0,
#             connection_test_amount=1,
#             connection_length=10)
#         print_results(results)
#     except Exception as e:
#         print(e)
#     try:
#         results["180x18x0"] = bench.repeat_test_connection(
#             rooted=rooted,
#             connect_from_ip=True,
#             recovery=recovery_type,
#             rounds=100,
#             sleep_between_connections=0,
#             connection_length=180,
#             connection_test_amount=18)
#         print_results(results)
#     except Exception as e:
#         print(e)
#     try:
#         results["180x1x0"] = bench.repeat_test_connection(
#             rooted=rooted,
#             connect_from_ip=True,
#             recovery=recovery_type,
#             rounds=100,
#             sleep_between_connections=0,
#             connection_length=180,
#             connection_test_amount=18)
#         print_results(results)
#     except Exception as e:
#         print(e)
#     try:
#         results["10x2x120"] = bench.repeat_test_connection(
#             rooted=rooted,
#             connect_from_ip=True,
#             recovery=recovery_type,
#             rounds=100,
#             sleep_between_connections=120,
#             connection_length=10,
#             connection_test_amount=2)
#         print_results(results)
#     except Exception as e:
#         print(e)
#     print(results)
#
#
# def print_results(res):
#     print("\n\n")
#     print(json.dumps(dict(res), indent=4, sort_keys=True))


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
    # main()
    b = ConnectionBenchmark()
    b.run(3, 1)
    for idx, stat in enumerate(b.stats):
        print("Stats[{}]".format(idx))
        for key in dir(stat):
            if not key.startswith('__'):
                print(key + ": " + str(getattr(stat, key)))
        print("\n")

