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



Other DeviceUtils methods:
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
from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary


def benchmark_dir_funcs(repeats, device):
    """
    benchmarks for mkdir and rmdir
    :param repeats:
    :param device:
    :return:
    """
    res_mkdir = []
    res_rmdir = []
    args = ["sdcard/Documents/bla"]
    for i in range(repeats):
        res_mkdir.append(time_it(device, "mkdir", args, expected=[True]))
        res_rmdir.append(time_it(device, "rmdir", args, expected=[True]))
    return res_mkdir, res_rmdir


def benchmark_touch_remove(repeats, device):
    """
    benchmarks for mkdir and rmdir
    :param repeats:
    :param device:
    :return:
    """
    res_touch = []
    res_remove = []
    args = ["sdcard/Documents/touched"]
    for i in range(repeats):
        res_touch.append(time_it(device, "touch", args, expected=[True]))
        res_remove.append(time_it(device, "remove", args, expected=[True]))
    return res_touch, res_remove


def benchmark_push_pull(repeats, device, size_bytes):
    """
    :param repeats:
    :param device:
    :param size:
    :return:
    """
    pc_path = "/tmp/tmp_file_%d"%size_bytes
    # create the file on the computer
    # todo
    device_path = "/sdcard/Documents/test_push_%d"%size_bytes
    push_args = [pc_path, device_path]
    pull_args = [device_path, pc_path]
    res_push = []
    res_pull = []
    for i in range(repeats):
        res_push.append(time_it(device, "push", push_args, [True]))
        res_pull.append(time_it(device, "pull", pull_args, [True]))

    # cleanup
    os.remove(pc_path)
    device.remove(device_path)

    return res_push, res_pull


def device_benchmark(device, repeats):
    """
    benchmark of all methods on device_utils for a specific device
    :type device: DeviceUtils
    :type repeats: int
    :return: None
    """
    benchmark_results = {}

    # benchmark the simplest methods (they don't require any special params or code)
    benchmark_results["send_intent"] = benchmark_it(repeats, device, "send_intent", ["my_action", "my_name"])  # todo reasonable params, check return value?
    benchmark_results["mkdir"], benchmark_results["rmdir"] = benchmark_dir_funcs(repeats, device)
    benchmark_results["touch"], benchmark_results["remove"] = benchmark_touch_remove(repeats, device)
    benchmark_results["ls"] = benchmark_it(repeats, device, "ls", ["/sdcard/Documents"])  # todo check return value?
    benchmark_results["get_time"] = benchmark_it(repeats, device, "get_time", [])
    benchmark_results["get_device_name"] = benchmark_it(repeats, device, "get_device_name", [])
    benchmark_results["get_prop"] = benchmark_it(repeats, device, "get_prop", ["sys.usb.config"], ["mtp,usb"])
    benchmark_results["set_prop"] = benchmark_it(repeats, device, "set_prop", ["sys.usb.config", '"mtp, usb"'])
    benchmark_results["is_earphone_connected"] = benchmark_it(repeats, device, "is_earphone_connected", [], [True,False])  # todo: request user to connect/disconnect earphone?
    benchmark_results["get_volume"] = benchmark_it(repeats, device, "get_volume", [], range(1, device.get_max_volume()))

    # create and print summary
    create_summary(benchmark_results)

    # benchmark set volume for all supported volumes
    set_volume_results = {}
    for i in range(1, device.get_max_volume()):
        set_volume_results["set_volume_%d"%i] = benchmark_it(repeats, device, "set_volume", [i], [True])
    # create and print summary
    create_summary(set_volume_results)

    # benchmark for push and pull files
    file_size_bytes = [0, 1000, 100000, 200000]  # todo: profile what we really need

    push_results = {}
    pull_results = {}
    push_pull_results = {}
    for size in file_size_bytes:
        push_results["push_%d"%size], pull_results["pull_%d" % size] = benchmark_push_pull(repeats, device, size)
    # create and print summary
    create_summary(push_pull_results)
