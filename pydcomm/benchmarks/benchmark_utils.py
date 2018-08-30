import time
import pandas as pd
import numpy as np


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

    start = time.time()
    ok = True
    try:
        res = getattr(obj, method)(*args, **kwargs)
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
        return ok, (time.time() - start)*1000.0


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

    df = pd.DataFrame(data,columns=columns).set_index(columns[0])
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
    n_ok = len([n for n in success if n is True])
    total = len(single_benchmark)
    return {
        "test_name": name,
        "speed_average_ms": np.average(times),
        "speed_min_ms": min(times),
        "speed_max_ms": max(times),
        "n_total": total,
        "n_pass": n_ok,
        "pass_rate": float(n_ok)/total,
        "n_fail": total - n_ok,
        "fail_rate": float(total - n_ok)/total,
    }


def create_summary(benchmark_results):
    """
    create a summary of the results and print them
    :type benchmark_results: dict<list<tuple<bool, float>>>
    """
    summaries = [get_stats(key, benchmark_results[key]) for key in benchmark_results.keys()]
    print_table(summaries)
