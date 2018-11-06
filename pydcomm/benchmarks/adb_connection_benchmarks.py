import pickle

import pandas as pd
import numpy as np
import time
from traceback import print_exc

import subprocess32
from enum import IntEnum

from pydcomm.benchmarks.raw_input_recorder import RawInputRecorder
from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
from pydcomm.general_android.connection.wired_adb_connection import AdbConnectionError, ConnectionClosedError

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


class ApiCallData(object):
    def __init__(self, type, total_time, success, manual_interactions_count, manual_times, failure_reason):
        self.type = type
        self.total_time = total_time
        self.success = success
        self.manual_interactions_count = manual_interactions_count
        self.manual_times = manual_times
        self.failure_reason = failure_reason

    def __repr__(self):
        return "{}, {}".format(type(self).__name__, self.__dict__)


class ConnectionBenchmark(object):
    def __init__(self):
        self.stats = []  # type: list[ApiCallData]

    def benchmark_adb(self, connection):
        success = False
        failure_reason = None
        start_time = time.time()
        input_recorder = RawInputRecorder(ignore_first=True)

        try:
            with input_recorder:
                success = connection.adb("shell echo hi") == "hi"
        except Exception as e:
            print(e.message)
            failure_reason = e
        finally:
            end_time = time.time()
            self.stats.append(ApiCallData("adb",  # type
                                          end_time - start_time,  # time
                                          success,  # success
                                          len(input_recorder.input_times),  # manual_interactions_count
                                          input_recorder.input_times,  # manual_times
                                          failure_reason))  # failure_reason
            return success

    def benchmark_connect(self):
        connection = None
        failure_reason = None
        start_time = time.time()
        input_recorder = RawInputRecorder(ignore_first=True)

        try:
            with input_recorder:
                connection = AdbConnectionFactory.get_oppo_wireless_device(use_manual_fixes=True)
        except Exception as e:
            print(e.message)
            failure_reason = e
            raise
        finally:
            end_time = time.time()
            self.stats.append(ApiCallData("connect",  # type
                                          end_time - start_time,  # time
                                          connection is not None,  # success
                                          len(input_recorder.input_times),  # manual_interactions_count
                                          input_recorder.input_times,  # manual_times
                                          failure_reason))  # failure_reason
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
            except ConnectionClosedError:
                success = True
        except Exception as e:
            failure_reason = e
        finally:
            if end_time is None:
                end_time = time.time()
            self.stats.append(ApiCallData("disconnect",  # type
                                          end_time - start_time,  # time
                                          success,  # success
                                          0,  # manual_interactions_count
                                          [],  # manual_times
                                          failure_reason))  # failure_reason
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
            print("Got exception. Aborting this run. Details:")
            print_exc(e)


class TestDefinition(object):
    def __init__(self, rounds, num_connection_checks, check_interval):
        self.rounds = rounds
        self.num_connection_checks = num_connection_checks
        self.check_interval = check_interval

    def __repr__(self):
        # Temporary
        return "{}x{}x{}".format(self.rounds, self.num_connection_checks, self.check_interval)
        # return "{} <num_connection_checks={}, check_interval={}>".format(self.__class__.__name__, self.num_connection_checks, self.check_interval)


class TestResult(object):
    def __init__(self, rounds, test_definition, success_count, timeout_exceptions, adb_connection_errors, total_manual_fix_count, median_fix_time):
        self.rounds = rounds
        self.test_definition = test_definition
        self.success_count = success_count
        self.timeout_exceptions = timeout_exceptions
        self.adb_connection_errors = adb_connection_errors
        self.total_manual_fix_count = total_manual_fix_count
        self.median_fix_time = median_fix_time

    def __repr__(self):
        return "{}, {}".format(type(self).__name__, self.__dict__)


tests = [
    # rounds, num_connection_checks, check_interval
    TestDefinition(100, 10, 0),
    TestDefinition(20, 2, 20),
    TestDefinition(100, 1, 1)
]


def flatten(l):
    return [item for sublist in l for item in sublist]


def print_table(test_results_summed):
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    columns = [
        "rounds",
        "test_definition",
        "success_count",
        "timeout_exceptions",
        "adb_connection_errors",
        "total_manual_fix_count",
        "median_fix_time",
    ]
    data = []
    for t in test_results_summed:
        row = [getattr(t, c) for c in columns]
        data.append(row)
    df = pd.DataFrame(data, columns=columns).set_index(columns[0])
    print (df)


def create_run_summary(runs):
    test_results_summed = []
    for i, run_result in enumerate(runs):
        flat = flatten(run_result)
        rounds = len(flat)
        success_count = len([x for x in flat if x.success])
        timeout_exceptions = len([x for x in flat if type(x.failure_reason) is subprocess32.TimeoutExpired])
        adb_connection_error = len([x for x in flat if type(x.failure_reason) is AdbConnectionError])
        total_manual_fix_count = sum([x.manual_interactions_count for x in flat])
        flat_manual_times = flatten([x.manual_times for x in flat])
        median_fix_time = np.median(flat_manual_times) if flat_manual_times else None
        result = TestResult(rounds, tests[i], success_count, timeout_exceptions, adb_connection_error, total_manual_fix_count, median_fix_time)
        test_results_summed.append(result)
    return test_results_summed


def run_rounds():
    runs = []
    try:
        for test in tests:
            run_results = []
            for i in range(test.rounds):
                b = ConnectionBenchmark()
                b.run(test.num_connection_checks, test.check_interval)
                run_results.append(b.stats)
            runs.append(run_results)
    except KeyboardInterrupt:
        pass
    return runs


def main():
    # Run with "<cmd> | ts [%H:%M:%S]'
    runs = run_rounds()
    with open("raw_data_" + time.strftime("%H:%M:%S") + ".pickle") as f:
        pickle.dump(runs, f)
    test_results_summed = create_run_summary(runs)
    print_table(test_results_summed)


if __name__ == "__main__":
    main()
