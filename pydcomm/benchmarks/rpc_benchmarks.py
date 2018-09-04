from pydcomm.benchmarks.benchmark_utils import pandas_config_for_bench
from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
import numpy as np
from collections import OrderedDict
import time
import tqdm
from pydcomm.rpc.marshallers import nparray_marshal, nparray_unmarshal

"""
Format:
                   total_times success_rate success auto_recover manual_recover fail min_speed_ms avg_speed_ms max_speed_ms
                                                                                                                           
rpc_echo_no_params         500          1.0     500            0              0    0         3000         5000        10000
rpc_echo_float             300         0.98     295            4              1    0        18000        22000        26000
rpc_echo_string            100         0.90      90           15             12   10        50000        60000       100000
rpc_echo_1k                100         0.90      90           15             12   10        50000        60000       100000
rpc_echo_100k              100         0.90      90           15             12   10        50000        60000       100000
rpc_echo_1M                 50         0.80      40            4              8   10        50000        60000       100000
rpc_echo_10M                20         0.75      15            2              4    5        50000        60000       100000
rpc_echo_100M                3         0.67       2            1              1    1        50000        60000       100000
"""


def rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, repeats):
    """
    Benchmark RPC echo with device for given params.
    :type name: str
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
    return benchmark_it(repeats, rpc, "call", ("_rpc_echo", params, marshaller, unmarshaller), expected=expected)


def call_benchmark(rpc, repeats=None):
    """
    Benchmarks the "call" method of rpcs.

    rpc instance must have an "echo" method on the server side, that echos back whatever it got.
    """
    name_to_stuff = OrderedDict()
    name_to_stuff['float'] = (1000, None, None, 8.2)
    name_to_stuff['string'] = (1000, None, None, 'Test TEST test!')
    name_to_stuff['1k'] = (500, nparray_marshal, nparray_unmarshal, np.random.rand(2 ** 10))
    name_to_stuff['100k'] = (100, nparray_marshal, nparray_unmarshal, np.random.rand(100 * 2 ** 10))
    name_to_stuff['1M'] = (50, nparray_marshal, nparray_unmarshal, np.random.rand(2 ** 20))
    name_to_stuff['10M'] = (10, nparray_marshal, nparray_unmarshal, np.random.rand(10 * 2 ** 20))
    name_to_stuff['100M'] = (3, nparray_marshal, nparray_unmarshal, np.random.rand(100 * 2 ** 20))

    benchmark_results = OrderedDict()
    for name, (reps, marshaller, unmarshaller, params) in name_to_stuff.items():
        if type(repeats) == dict and name in repeats:
            reps = repeats[name]
        if type(repeats) in (int, float):
            reps = repeats
        benchmark_results[name] = rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, reps)

    pandas_config_for_bench()
    create_summary(benchmark_results)

