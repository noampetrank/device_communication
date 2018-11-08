import pickle
import time
from traceback import print_exc

import numpy as np
import pandas as pd
import subprocess32

from pydcomm.benchmarks.benchmark_utils import flatten, BetterTee
from pydcomm.benchmarks.connection.data import ApiCallData, TestDefinition, PerCallTestResult, TestResult
from pydcomm.benchmarks.raw_input_recorder import RawInputRecorder
from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
from pydcomm.general_android.connection.wired_adb_connection import AdbConnectionError, ConnectionClosedError, ConnectingError


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


tests = [
    # rounds, num_connection_checks, check_interval
    TestDefinition(20, 5, 0),
    TestDefinition(7, 2, 20),
    TestDefinition(20, 1, 1)
]


def print_table(test_results_summed):
    """

    :type test_results_summed: list[pydcomm.benchmarks.connection.data.TestResult]
    :return:
    """
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
        "connection_failed",

        "connect_data.total_calls",
        "connect_data.mean_time",
        "connect_data.mean_manual_fix_time",
        "connect_data.success_amount",
        "connect_data.manual_fix_pct",
        "connect_data.adb_connection_error_pct",
        "connect_data.timeout_error_pct",

        "adb_data.total_calls",
        "adb_data.mean_time",
        "adb_data.mean_manual_fix_time",
        "adb_data.success_amount",
        "adb_data.manual_fix_pct",
        "adb_data.adb_connection_error_pct",
        "adb_data.timeout_error_pct",

        "disconnect_data.total_calls",
        "disconnect_data.mean_time",
        "disconnect_data.mean_manual_fix_time",
        "disconnect_data.success_amount",
        "disconnect_data.manual_fix_pct",
        "disconnect_data.adb_connection_error_pct",
        "disconnect_data.timeout_error_pct",
    ]
    data = []
    for result in test_results_summed:
        row = [getattr(result, col) if col.find(".") == -1 else getattr(getattr(result, col.split(".")[0]), col.split(".")[1]) for col in columns]
        data.append(row)
    df = pd.DataFrame(data, columns=columns).set_index(columns[0])
    print (df)


def get_call_stats(call_type, flat):
    """

    :type call_type: str
    :type flat: list[ApiCallData]
    :return:
    """
    calls_of_type = [x for x in flat if x.type == call_type]
    total_calls = len(calls_of_type)
    mean_time = np.average([x.total_time for x in calls_of_type])
    mean_manual_fix_time = np.average(flatten([x.manual_times for x in calls_of_type]))
    success_amount = len([x for x in calls_of_type if x.success])
    manual_fix_pct = float(len([x for x in calls_of_type if x.manual_interactions_count])) / total_calls
    adb_connection_error_pct = float(len([x for x in calls_of_type if type(x.failure_reason) is AdbConnectionError])) / total_calls
    timeout_error_pct = float(len([x for x in calls_of_type if type(x.failure_reason) is subprocess32.TimeoutExpired])) / total_calls
    return PerCallTestResult(total_calls=total_calls,
                             mean_time=mean_time,
                             mean_manual_fix_time=mean_manual_fix_time,
                             success_amount=success_amount,
                             manual_fix_pct=manual_fix_pct,
                             adb_connection_error_pct=adb_connection_error_pct,
                             timeout_error_pct=timeout_error_pct)


def create_run_summary(runs):
    test_results_summed = []
    for i, run_result in enumerate(runs):
        flat = flatten(run_result)
        rounds = len(flat)
        adb_connection_error, median_fix_time, success_count, timeout_exceptions, total_manual_fix_count, connection_failed = get_general_stats(flat)
        result = TestResult(
            rounds,
            tests[i],
            success_count,
            timeout_exceptions,
            adb_connection_error,
            total_manual_fix_count,
            median_fix_time,
            connection_failed,
            get_call_stats("connect", flat),
            get_call_stats("adb", flat),
            get_call_stats("disconnect", flat),
        )
        test_results_summed.append(result)
    return test_results_summed


def get_general_stats(flat):
    success_count = len([x for x in flat if x.success])
    timeout_exceptions = len([x for x in flat if type(x.failure_reason) is subprocess32.TimeoutExpired])
    adb_connection_error = len([x for x in flat if type(x.failure_reason) is AdbConnectionError or type(x.failure_reason) is ConnectingError])
    connection_failed = len([x for x in flat if type(x.failure_reason) is AttributeError])
    total_manual_fix_count = sum([x.manual_interactions_count for x in flat])
    flat_manual_times = flatten([x.manual_times for x in flat])
    median_fix_time = np.median(flat_manual_times) if flat_manual_times else None
    return adb_connection_error, median_fix_time, success_count, timeout_exceptions, total_manual_fix_count, connection_failed


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
    from pybuga.infra.utils.buga_utils import indent_printing
    start_time_string = time.strftime("%H:%M:%S")
    with BetterTee("run_{}.log".format(start_time_string)):
        with indent_printing(lambda: time.strftime('[%H:%M:%S] ')):
            runs = run_rounds()
            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
                pickle.dump(runs, f)
            test_results_summed = create_run_summary(runs)
            print_table(test_results_summed)


if __name__ == "__main__":
    main()
