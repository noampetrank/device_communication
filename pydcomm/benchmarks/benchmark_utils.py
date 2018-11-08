import sys
import time
import pandas as pd
import numpy as np
import timeit

import timeit
import time

# https://stackoverflow.com/a/24812460/365408
# set timeit to return the value
from pybuga.tests.utils.test_helpers import Tee


def _template_func(setup, func):
    """Create a timer function. Used if the "statement" is a callable."""

    def inner(_it, _timer, _func=func):
        setup()
        _t0 = _timer()
        for _i in _it:
            retval = _func()
        _t1 = _timer()
        return _t1 - _t0, retval

    return inner


timeit._template_func = _template_func


def new_time_it(action, expected=None, repeats=1):
    """
    Takes a lambda as action, an expected value to assert against,
    and the number of repaets, and returns the amount of time the
    statement takes and whether the expected value is received.
    :param action: lambda to measure
    :param expected: expected value, pass None to not assert
    :param repeats: How many times
    :return: list of tuples containins time it took and whether the assert succeded.
    """
    if expected:
        return timeit.repeat(lambda: action() == expected, repeat=repeats)
    else:
        return [(x, True) for x, _ in timeit.repeat(lambda: action(), repeat=repeats)]


def time_it(obj, method, args, expected=None, kwargs=None):
    """
    run a method on the object and time it.
    todo: test this

    :param expected: None, iterable of options, or function that evaluates on result and returns bool.
    :type expected: Union[NoneType, list, (T) -> bool]
    :type obj: object
    :type method: str
    :type args: list
    :rtype: tuple<bool, float>
    """
    if kwargs is None:
        kwargs = {}

    ok = True
    start = 0
    end = None
    method = getattr(obj, method)
    try:
        start = time.time()
        res = method(*args, **kwargs)
        end = time.time()
        # if we got expected return value(s) check against them
        if expected is None:
            ok = True
        else:
            try:
                ok = expected(res)
            except:
                ok = res in expected
    except:
        ok = False
    finally:
        end = end or time.time()
        return ok, (end - start) * 1000.0


def benchmark_it(repeats, obj, method, args, expected=None, kwargs=None):
    """
    Time a method repeatedly, return time and success code for each run
    :type repeats: int
    :type expected: list
    :type obj: object
    :type method: str
    :type args: list
    :rtype: list<tuple<bool, float>>
    """
    res = []
    for i in range(repeats):
        res.append(time_it(obj, method, args, expected=expected, kwargs=kwargs))
    return res


def print_table(summaries):
    """
    load the summary into pandas and print it
    :type summaries: list<dict>
    :return:
    """
    columns = 'test_name speed_avg_ms speed_min_ms speed_max_ms n_pass pass_rate n_fail fail_rate n_total'.split()
    data = []
    for s in summaries:
        data.append([s["test_name"],
                     s["speed_average_ms"],
                     s["speed_min_ms"],
                     s["speed_max_ms"],
                     s["n_pass"],
                     s["pass_rate"],
                     s["n_fail"],
                     s["fail_rate"],
                     s["n_total"]])

    data = sorted(data)
    df = pd.DataFrame(data, columns=columns).set_index(columns[0])
    print(df)


def get_stats(name, single_benchmark):
    """
    get stats for a benchmark
    :type name: str
    :type single_benchmark: list<tuple<bool, float>>
    :rtype: dict
    """
    times = [n[1] for n in single_benchmark]
    success = [n[0] for n in single_benchmark]
    n_ok = len([n for n in success if n])
    total = len(single_benchmark)
    return {
        "test_name": name,
        "speed_average_ms": np.average(times),
        "speed_min_ms": min(times),
        "speed_max_ms": max(times),
        "n_total": total,
        "n_pass": n_ok,
        "pass_rate": float(n_ok) / total,
        "n_fail": total - n_ok,
        "fail_rate": float(total - n_ok) / total,
    }


def create_summary(benchmark_results):
    """
    create a summary of the results and print them
    :type benchmark_results: dict<list<tuple<bool, float>>>
    """
    summaries = [get_stats(key, benchmark_results[key]) for key in benchmark_results.keys()]
    print_table(summaries)


def pandas_config_for_bench():
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 100)
    pd.set_option('display.width', 160)
    pd.set_option('display.max_colwidth', 32)


def flatten(l):
    return [item for sublist in l for item in sublist]


class BetterTee(Tee):
    def __init__(self, name, stderr=False):
        super(BetterTee, self).__init__(name)
        self.use_stderr = stderr

    def __enter__(self):
        if self.use_stderr:
            self.old_stdout = sys.stderr
            sys.stderr = self
        else:
            self.old_stdout = sys.stdout
            sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
