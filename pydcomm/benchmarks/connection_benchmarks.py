"""
========================== Format: ==========================
Push file:
                speed_min_ms speed_avg_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total
test_name
push_empty_file         10.0         25.3        208.1    198      0.99      2      0.01     200
push_1kB                12.0         27.3        238.1     98      0.98      2      0.02     100
push_1MB               100.0        250.3       2080.1      7       0.7      3       0.3      10
push_100MB            1000.0       2500.3      20800.1      2      0.67      1      0.33       3
push_1GB                 nan          nan          nan      0       0.0      1       1.0       1



Pull file:
                speed_min_ms speed_avg_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total
test_name
pull_empty_file         10.0         25.3        208.1    198      0.99      2      0.01     200
pull_1kB                12.0         27.3        238.1     98      0.98      2      0.02     100
pull_1MB               100.0        250.3       2080.1      7       0.7      3       0.3      10
pull_100MB            1000.0       2500.3      20800.1      2      0.67      1      0.33       3
pull_1GB                 nan          nan          nan      0       0.0      1       1.0       1



Push+pull file:
                     speed_min_ms speed_avg_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total
test_name
push_pull_empty_file         10.0         25.3        208.1    198      0.99      2      0.01     200
push_pull_1kB                12.0         27.3        238.1     98      0.98      2      0.02     100
push_pull_1MB               100.0        250.3       2080.1      7       0.7      3       0.3      10
push_pull_100MB            1000.0       2500.3      20800.1      2      0.67      1      0.33       3
push_pull_1GB                 nan          nan          nan      0       0.0      1       1.0       1



Set volume:
          speed_min_ms speed_avg_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total
test_name
volume_0          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_1          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_2          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_3          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_4          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_5          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_6          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_7          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_8          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_9          10.0         25.3        208.1    198      0.99      2      0.01     200
volume_10         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_11         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_12         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_13         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_14         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_15         10.0         25.3        208.1    198      0.99      2      0.01     200
volume_16         10.0         25.3        208.1    198      0.99      2      0.01     200



Other AndroidDeviceUtils methods:
                      speed_min_ms speed_avg_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total
test_name
send_intent                   10.0         25.3        208.1    198      0.99      2      0.01     200
mkdir                         10.0         25.3        208.1    198      0.99      2      0.01     200
touch_file                    10.0         25.3        208.1    198      0.99      2      0.01     200
ls                            10.0         25.3        208.1    198      0.99      2      0.01     200
get_time                      10.0         25.3        208.1    198      0.99      2      0.01     200
remove                        10.0         25.3        208.1    198      0.99      2      0.01     200
get_device_name               10.0         25.3        208.1    198      0.99      2      0.01     200
get_prop                      10.0         25.3        208.1    198      0.99      2      0.01     200
set_prop                      10.0         25.3        208.1    198      0.99      2      0.01     200
is_earphone_connected         10.0         25.3        208.1    198      0.99      2      0.01     200
is_max_volume                 10.0         25.3        208.1    198      0.99      2      0.01     200
"""
import os

from pydcomm.general_android.connection.connection import DummyBugaConnection

from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
from tqdm import tqdm


def benchmark_push_pull(repeats, connection, size_bytes, use_tqdm=False):
    """
    :param repeats:
    :param connection:
    :param size_bytes: size of random data or the random data itself
    :param bool use_tqdm: Whether or not to show a progress bar.
    :return:
    """
    if type(size_bytes) == str:
        data = size_bytes
        size_bytes = len(data)
    else:
        data = os.urandom(size_bytes)

    # create the file on the computer
    pc_path = "/tmp/tmp_file_%d" % size_bytes
    with open(pc_path, 'w') as f:
        f.write(data)

    device_path = "/sdcard/Documents/test_push_%d" % size_bytes
    push_args = [pc_path, device_path]
    pull_args = [device_path, pc_path]
    res_push = []
    res_pull = []
    if use_tqdm:
        iters = tqdm(range(repeats), desc='Iteration', position=1)
    else:
        iters = range(repeats)
    for _ in iters:
        res_push.append(time_it(connection, "push", push_args, [True]))
        res_pull.append(time_it(connection, "pull", pull_args, [True]))

    # cleanup
    os.remove(pc_path)
    connection.shell("rm %s" % device_path)

    return res_push, res_pull


def all_benchmarks(connection, repeats):
    """
    benchmark of all methods on device_utils for a specific device
    :type connection:
    :type repeats: int
    :return: None
    """
    # benchmark for push and pull files
    file_size_bytes = [0, 1000, 100000, 200000]  # todo: profile what we really need

    push_results = {}
    pull_results = {}
    push_pull_results = {}
    for size in file_size_bytes:
        push_results["push_%d" % size], pull_results["pull_%d" % size] = benchmark_push_pull(repeats, connection, size)
    # create and print summary
    create_summary(dict(push_results, **pull_results))


def main():
    connection = DummyBugaConnection()

    import pandas as pd
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 20000)
    all_benchmarks(connection, 1)


if __name__ == '__main__':
    main()
