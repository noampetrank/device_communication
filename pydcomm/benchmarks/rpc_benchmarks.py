from pydcomm.benchmarks.benchmark_utils import pandas_config_for_bench
from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
import numpy as np
from collections import OrderedDict
import time
import tqdm
import os
from pydcomm.rpc.marshallers import nparray_marshal, nparray_unmarshal

"""
Format:
           speed_avg_ms  speed_min_ms  speed_max_ms  n_pass  pass_rate  n_fail  fail_rate  n_total
test_name                                                                                         
float          0.089372      0.083923      0.288010    1000        1.0       0        0.0     1000
string         0.091907      0.084877      0.277996    1000        1.0       0        0.0     1000
1k             0.212770      0.192881      0.360966     500        1.0       0        0.0      500
100k          10.655496      9.881020     12.848139     100        1.0       0        0.0      100
1M           117.582521    104.593039    141.941071      50        1.0       0        0.0       50
10M         1414.263058   1390.681982   1459.050894      10        1.0       0        0.0       10
100M       14249.854247  14118.469000  14508.166790       3        1.0       0        0.0        3
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
    name_to_stuff['ndarray'] = (500, nparray_marshal, nparray_unmarshal, np.random.rand(2 ** 8))
    name_to_stuff['1k'] = (500, None, None, os.urandom(2 ** 10))
    name_to_stuff['100k'] = (100, None, None, os.urandom(100 * 2 ** 10))
    name_to_stuff['1M'] = (50, None, None, os.urandom(2 ** 20))
    name_to_stuff['10M'] = (10, None, None, os.urandom(10 * 2 ** 20))
    name_to_stuff['100M'] = (3, None, None, os.urandom(100 * 2 ** 20))

    benchmark_results = OrderedDict()
    for name, (reps, marshaller, unmarshaller, params) in name_to_stuff.items():
        if type(repeats) == dict and name in repeats:
            reps = repeats[name]
        if type(repeats) in (int, float):
            reps = repeats
        benchmark_results[name] = rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, reps)

    pandas_config_for_bench()
    create_summary(benchmark_results)

