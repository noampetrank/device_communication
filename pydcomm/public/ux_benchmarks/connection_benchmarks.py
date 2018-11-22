import pickle
import time
import sys
from traceback import print_exc
from collections import namedtuple

import numpy as np
import pandas as pd
import subprocess32
from enum import IntEnum
from pybuga.tests.utils.test_helpers import Tee
from pybuga.infra.utils.user_input import UserInput
from pydcomm.public.iconnection import (ConnectionError, ConnectionClosedError,
                                        all_connection_factories)

from pydcomm.benchmarks.raw_input_recorder import RawInputRecorder


class Recovery(IntEnum):
    NONE = 0
    AUTO = 1
    INTERACTIVE = 2


ApiCallData = namedtuple("ApiCallData", "type total_time success manual_interactions_count manual_times failure_reason")


class ConnectionBenchmark(object):
    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

        self.stats = []
        """@type: list[ApiCallData]"""

    def benchmark_connect(self):
        connection = None
        failure_reason = None
        start_time = time.time()
        input_recorder = RawInputRecorder(ignore_first=True)

        try:
            with input_recorder:
                connection = self.connection_factory()
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

    def benchmark_shell(self, connection):
        success = False
        failure_reason = None
        start_time = time.time()
        input_recorder = RawInputRecorder(ignore_first=True)

        try:
            with input_recorder:
                success = connection.shell("echo hi") == "hi"
        except Exception as e:
            print(e.message)
            failure_reason = e
        finally:
            end_time = time.time()
            self.stats.append(ApiCallData("shell",  # type
                                          end_time - start_time,  # time
                                          success,  # success
                                          len(input_recorder.input_times),  # manual_interactions_count
                                          input_recorder.input_times,  # manual_times
                                          failure_reason))  # failure_reason
            return success

    def benchmark_disconnect(self, connection):
        """
        :param pydcomm.general_android.connection.IConnection connection: Connection to disconnect.
        :return:
        """
        success = False
        failure_reason = None
        end_time = None
        start_time = time.time()

        try:
            connection.disconnect()
            end_time = time.time()

            # Expect that adb raises exception
            try:
                connection.disconnect()
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
                self.benchmark_shell(connection)
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

    def __str__(self):
        # Temporary
        return "{}x{}x{}".format(self.rounds, self.num_connection_checks, self.check_interval)
        # return "{} <num_connection_checks={}, check_interval={}>".format(self.__class__.__name__,
        # self.num_connection_checks, self.check_interval)


class TestResult(object):
    def __init__(self, rounds, test_definition, success_count, timeout_exceptions, adb_connection_errors,
                 total_manual_fix_count, median_fix_time):
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
    TestDefinition(20, 5, 0),
    TestDefinition(7, 2, 20),
    TestDefinition(20, 1, 1)
]


def flatten(l):
    return [item for sublist in l for item in sublist]


def print_table(connection_factory_name, conn_type, test_results_summed):
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

    print 'Summary for connection factory: {}'.format(connection_factory_name)
    print 'connection o type "{}"'.format(conn_type)

    print df


def create_run_summary(runs):
    test_results_summed = []
    for i, run_result in enumerate(runs):
        flat = flatten(run_result)
        rounds = len(flat)
        success_count = len([x for x in flat if x.success])
        timeout_exceptions = len([x for x in flat if type(x.failure_reason) is subprocess32.TimeoutExpired])
        adb_connection_error = len([x for x in flat if type(x.failure_reason) is ConnectionError])
        total_manual_fix_count = sum([x.manual_interactions_count for x in flat])
        flat_manual_times = flatten([x.manual_times for x in flat])
        median_fix_time = np.median(flat_manual_times) if flat_manual_times else None
        result = TestResult(rounds, tests[i], success_count, timeout_exceptions, adb_connection_error,
                            total_manual_fix_count, median_fix_time)
        test_results_summed.append(result)
    return test_results_summed


def run_rounds(connection_factory):
    runs = []
    try:
        for test in tests:
            run_results = []
            for i in range(test.rounds):
                b = ConnectionBenchmark(connection_factory)
                b.run(test.num_connection_checks, test.check_interval)
                run_results.append(b.stats)
            runs.append(run_results)
    except KeyboardInterrupt:
        pass
    return runs


# TODO: Extract code from pybuga to someplace else
class BetterTee(Tee):
    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout


def main():
    from pybuga.infra.utils.buga_utils import indent_printing
    start_time_string = time.strftime("%H:%M:%S")
    with BetterTee("run_{}.log".format(start_time_string)):
        with indent_printing.time():
            # from functools import partial
            # from pydcomm.general_android.connection.connection_factory import AdbConnectionFactory
            # connection_factory = partial(AdbConnectionFactory.get_oppo_wireless_device, use_manual_fixes=True)

            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_connection_factories.keys(), False)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            connection_factory = all_connection_factories[factory_name]

            print "Choose connection type:"
            conn_type = UserInput.menu(["wired", "wireless"], False)
            if conn_type is None:
                print "Thanks, goodbye!"
                return

            connection_factory_method = getattr(connection_factory, conn_type + "_connection")

            runs = run_rounds(connection_factory_method)
            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
                pickle.dump((connection_factory.__name__, conn_type, runs), f)
            test_results_summed = create_run_summary(runs)
            print_table(connection_factory.__name__, conn_type, test_results_summed)


def test_main():
    import mock
    import __builtin__

    @mock.patch.object(__builtin__, "raw_input")
    @mock.patch.object(time, "sleep")
    def call_main(msleep, mraw_input):
        msleep.return_value = None
        mraw_input.side_effect = ["dummy", "wired"]
        main()

    call_main()


if __name__ == "__main__":
    main()
