from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
import numpy as np
import time
import tqdm

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
    return benchmark_it(repeats, rpc, "call", ("echo", params, marshaller, unmarshaller), expected=lambda res: np.all(res == params))


def call_benchmark(rpc, repeats=None):
    """
    Benchmarks the "call" method of rpcs.

    rpc instance must have an "echo" method on the server side, that echos back whatever it got.
    """
    name_to_stuff = {
        'float': (1000, float_marshaller, float_unmarshaller, 8.2),
        'string': (1000, string_marshaller, string_unmarshaller, 'Test TEST test!'),
        '1k': (500, nparray_marshaller, nparray_unmarshaller, np.random.rand(2 ** 10)),
        '100k': (100, nparray_marshaller, nparray_unmarshaller, np.random.rand(100 * 2 ** 10)),
        '1M': (50, nparray_marshaller, nparray_unmarshaller, np.random.rand(2 ** 20)),
        '10M': (10, nparray_marshaller, nparray_unmarshaller, np.random.rand(10 * 2 ** 20)),
        '100M': (3, nparray_marshaller, nparray_unmarshaller, np.random.rand(100 * 2 ** 20)),
    }
    benchmark_results = {}
    for name, (reps, marshaller, unmarshaller, params) in name_to_stuff.items():
        if type(repeats) == dict and name in repeats:
            reps = repeats[name]
        if type(repeats) in (int, float):
            reps = repeats
        benchmark_results[name] = rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, reps)
    
    create_summary(benchmark_results)
