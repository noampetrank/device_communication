from pydcomm.benchmarks.benchmark_utils import pandas_config_for_bench
from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
import numpy as np
from collections import OrderedDict
import time
from tqdm import tqdm
import os
from pydcomm.rpc._marshallers import cbor_marshal, cbor_unmarshal, nparray_marshal, nparray_unmarshal

"""
Format:

RPC send data:
           speed_avg_ms  speed_min_ms  speed_max_ms  n_pass  pass_rate  n_fail  fail_rate  n_total
test_name                                                                                         
float          8.784111      1.859903    336.040974    1000        1.0       0        0.0     1000
string        10.090166      2.164125    719.562054    1000        1.0       0        0.0     1000
ndarray       14.172284      2.917051    427.799940     500        1.0       0        0.0      500
1k            19.564796      2.265930    382.502079     500        1.0       0        0.0      500
100k          26.730566      9.194136    641.997099     100        1.0       0        0.0      100
1M           178.978391     77.508926    743.016005      50        1.0       0        0.0       50
10M          593.276501    450.862885    941.382885      10        1.0       0        0.0       10
100M        5727.115313   4960.855961   7149.765968       3        1.0       0        0.0        3

RPC receive data:
           speed_avg_ms  speed_min_ms  speed_max_ms  n_pass  pass_rate  n_fail  fail_rate  n_total
test_name                                                                                         
float         10.541207      1.871824    358.628035    1000        1.0       0        0.0     1000
string         8.898913      2.090931    477.747917    1000        1.0       0        0.0     1000
ndarray       25.760884      4.681826    579.813004     500        1.0       0        0.0      500
1k            19.585879      2.290010    354.512930     500        1.0       0        0.0      500
100k          40.192955     15.449047    398.961067     100        1.0       0        0.0      100
1M           246.199927    108.092070    933.856964      50        1.0       0        0.0       50
10M         1126.785111    967.238903   1635.308027      10        1.0       0        0.0       10
100M       11213.354985  10464.277983  11909.776926       3        1.0       0        0.0        3

ADB push file:
           speed_avg_ms  speed_min_ms  speed_max_ms  n_pass  pass_rate  n_fail  fail_rate  n_total
test_name                                                                                         
string        11.027356      2.294779    861.882925    1000        1.0       0        0.0     1000
1k            21.090288      1.666069    614.458084     500        1.0       0        0.0      500
100k          34.826958     11.958122    433.668852     100        1.0       0        0.0      100
1M            98.230138     47.788143    364.906788      50        1.0       0        0.0       50
10M          626.329899    493.022919    944.319010      10        1.0       0        0.0       10
100M        6031.162262   5094.709873   6543.799877       3        1.0       0        0.0        3

ADB pull file:
           speed_avg_ms  speed_min_ms  speed_max_ms  n_pass  pass_rate  n_fail  fail_rate  n_total
test_name                                                                                         
string         7.928626      2.014875    328.226089    1000        1.0       0        0.0     1000
1k            14.490119      1.734018    460.376978     500        1.0       0        0.0      500
100k          38.246782     15.706778    397.205114     100        1.0       0        0.0      100
1M           150.368571     85.578918    343.545914      50        1.0       0        0.0       50
10M         1266.217494    938.235998   1845.056057      10        1.0       0        0.0       10
100M       11229.986986  10719.810963  11760.215044       3        1.0       0        0.0        3
"""


def rpc_echo_benchmark_for_params(rpc, params, marshaller, unmarshaller, repeats):
    """
    Benchmark RPC echo with device for given params.
    :type rpc: RemoteProcedureCaller
    :type params: marshallable
    :type marshaller: function or None
    :type unmarshaller: function or None
    :type repeats: int
    :rtype: dict
    """
    expected = lambda res: res == params
    if type(params) == np.ndarray:
        expected = lambda res: np.all(res == params)

    res_push, res_pop = [], []
    for i in tqdm(range(repeats), desc='Iteration', position=1):
        res_push.append(time_it(rpc, "call", ("_rpc_echo_push", params, marshaller, None), expected=('OK',)))
        res_pop.append(time_it(rpc, "call", ("_rpc_echo_pop", params, None, unmarshaller), expected=expected))

    return res_push, res_pop


def _adb_push_pull_benchmark_for_params(params, repeats):
    from pydcomm.general_android.adb_connection import AdbConnection
    from pydcomm.general_android.android_device_utils import AndroidDeviceUtils
    connection = AdbConnection()
    device_utils = AndroidDeviceUtils(connection)

    from pydcomm.benchmarks.android_device_utils_benchmarks import benchmark_push_pull
    return benchmark_push_pull(repeats, device_utils, params)


def call_benchmark(rpc, repeats=None, compare_to_adb=False):
    """
    Benchmarks the "call" method of rpcs.

    rpc instance must have an "echo" method on the server side, that echos back whatever it got.
    """
    name_to_stuff = OrderedDict()
    name_to_stuff['float'] = (1000, cbor_marshal, cbor_unmarshal, 8.2)
    name_to_stuff['string'] = (1000, None, None, 'Test TEST test!')
    name_to_stuff['ndarray'] = (500, nparray_marshal, nparray_unmarshal, np.random.rand(2 ** 8))
    name_to_stuff['1k'] = (500, None, None, os.urandom(2 ** 10))
    name_to_stuff['100k'] = (100, None, None, os.urandom(100 * 2 ** 10))
    name_to_stuff['1M'] = (50, None, None, os.urandom(2 ** 20))
    name_to_stuff['10M'] = (10, None, None, os.urandom(10 * 2 ** 20))
    name_to_stuff['100M'] = (3, None, None, os.urandom(100 * 2 ** 20))

    benchmark_result_push, benchmark_result_pop = OrderedDict(), OrderedDict()
    benchmark_result_adb_push, benchmark_result_adb_pull = OrderedDict(), OrderedDict()
    for name, (reps, marshaller, unmarshaller, params) in tqdm(name_to_stuff.items(), desc='Test', position=0):
        if type(repeats) == dict and name in repeats:
            reps = repeats[name]
        if type(repeats) in (int, float):
            reps = repeats

        benchmark_result_push[name], benchmark_result_pop[name] = rpc_echo_benchmark_for_params(rpc, params, marshaller, unmarshaller, reps)

        if compare_to_adb and marshaller is unmarshaller is None:
            benchmark_result_adb_push[name], benchmark_result_adb_pull[name] = rpc_echo_benchmark_for_params(rpc, params, marshaller, unmarshaller, reps)

    pandas_config_for_bench()
    print("RPC send data:")
    create_summary(benchmark_result_push)
    print("\nRPC receive data:")
    create_summary(benchmark_result_pop)
    if compare_to_adb:
        print("\nADB push file:")
        create_summary(benchmark_result_adb_push)
        print("\nADB pull file:")
        create_summary(benchmark_result_adb_pull)


if __name__ == "__main__":
    import re, subprocess
    ifconfig = subprocess.check_output("adb shell ifconfig", shell=True)
    ips = re.findall('Link encap:Ethernet[^\n]+\n[^\n]*inet addr:(\d+\.\d+\.\d+\.\d+)', ifconfig, re.M | re.S) or re.findall('wlan[^\n]+Link encap:[^\n]+\n[^\n]*inet addr:(\d+\.\d+\.\d+\.\d+)', ifconfig, re.M | re.S)
    if not ips:
        print("Can't get device IP")
    else:
        host_port = '{}:60004'.format(ips[0])
        print('Connecting to RPC server ' + host_port)
        from pydcomm.rpc._buga_grpc_caller import BugaGRpcCaller
        caller = BugaGRpcCaller(host_port)
        caller.start()
        print('Running benchmark')
        call_benchmark(caller, compare_to_adb=True)
