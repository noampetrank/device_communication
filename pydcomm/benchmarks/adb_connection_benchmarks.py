import __builtin__
import time

import mock
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


class ConnectionBenchmark(object):
    def __init__(self):
        self.stats = []  # type: list[ApiCallData]

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

    @mock.patch.object(__builtin__, 'raw_input')
    def benchmark_connect(self, mock_raw_input):
        input_recorder = RawInputRecorder()
        mock_raw_input.side_effect = input_recorder

        connection = None
        failure_reason = None
        start_time = time.time()

        try:
            connection = AdbConnectionFactory.get_oppo_wireless_device(use_manual_fixes=False)
        except Exception as e:
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
            print("Got exception. Aborting this run. Details: " + e.__class__.__name__ + ": " + e.message)


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
    b.run(num_connection_checks=3, check_interval=1)
    for idx, stat in enumerate(b.stats):
        print("Stats[{}]".format(idx))
        for key in dir(stat):
            if not key.startswith('__'):
                print(key + ": " + str(getattr(stat, key)))
        print("\n")
