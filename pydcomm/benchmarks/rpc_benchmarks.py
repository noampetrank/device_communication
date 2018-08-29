from pydcomm.benchmarks.benchmark_utils import time_it, benchmark_it, create_summary
import numpy as np

"""
"""


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


def rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, repeats):
    """
    Benchmark RPC echo with device for given params.
    :type name: str
    :type rpc: RemoteProcedureCaller
    :type params: marshallable
    :type marshaller: function or None
    :type unmarshaller: function or None
    :type repeats: int
    :rtype: pandas.DataFrame
    """



def device_benchmark(rpc, repeats=None):
    name_to_stuff = {
        'float': (1000, float_marshaller, float_unmarshaller, lambda: 8.2),
        'string': (1000, string_marshaller, string_unmarshaller, lambda: 'Test TEST test!'),
        '1k': (500, nparray_marshaller, nparray_unmarshaller, lambda: np.random.rand(2 ** 10)),
        '100k': (100, nparray_marshaller, nparray_unmarshaller, lambda: np.random.rand(100 * 2 ** 10)),
        '1M': (50, nparray_marshaller, nparray_unmarshaller, lambda: np.random.rand(2 ** 20)),
        '10M': (10, nparray_marshaller, nparray_unmarshaller, lambda: np.random.rand(10 * 2 ** 20)),
        '100M': (3, nparray_marshaller, nparray_unmarshaller, lambda: np.random.rand(100 * 2 ** 20)),
    }
    benchmark_results = {}
    for name, (reps, marshaller, unmarshaller, gen_params) in name_to_stuff.items():
        params = gen_params()
        if type(repeats) == dict and name in repeats:
            reps = repeats[name]
        if type(repeats) in (int, float):
            reps = repeats
        benchmark_results[name] = rpc_echo_benchmark_for_params(name, rpc, params, marshaller, unmarshaller, reps)
    #...
