import cPickle
from itertools import chain
import time

import numpy as np
import pybuga.infra.utils.config as config
from pybuga.infra.utils.buga_utils import indent_printing
from pybuga.infra.utils.user_input import UserInput
from pydcomm.public.connfactories import all_connection_factories
from pydcomm.public.ux_benchmarks.connection.scenarios import get_complete_benchmark
from pydcomm.public.ux_benchmarks.rpc_ux_benchmarks import BetterTee
from pydcomm.public.ux_benchmarks.utils import run_scenario


def single_api_call_summary(api_call, params=None, ret=None, additional=None, exception=None, ignore_first_manual=True):
    res = {
        "function_name": api_call.function_name,
        "call_time": api_call.end_time - api_call.start_time,
        "manual_fixes_count": len(api_call.manual_times),
        "manual_fixes_time": sum([end - start for start, end in api_call.manual_times[ignore_first_manual:]]),
        "is_exception": api_call.is_exception,
        "is_automatic": len(api_call.manual_times) == 0,
        "parameters": params
    }

    additional_columns = []
    if additional:
        res.update(additional)
        additional_columns = additional.keys()

    return res, additional_columns


def print_run_summary(conn_factory_name, stats, params, ret_val, additionals, print_all=False):
    """
    :param str conn_factory_name:
    :param stats:
    :param list[tuple] params:
    :param list[Any] ret_val:
    :param list[dict] additionals:
    :param bool print_all:
    """
    import pandas as pd
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    all_calls_raw = [single_api_call_summary(call, p, ret, add) for call, p, ret, add in
                     zip(stats, params, ret_val, additionals)]

    all_calls_raw, additional_columns = zip(*all_calls_raw)

    all_calls_table = pd.DataFrame(list(all_calls_raw)).set_index(['function_name'])
    summary_per_function = pd.DataFrame(all_calls_table).assign(total_calls=1)

    aggregates = get_aggregates(additional_columns)
    summary_per_function["success_rate"] = (~summary_per_function.is_exception).astype(float)
    summary_per_function = summary_per_function.astype({
        "is_exception": float,
        "is_automatic": float,
    })  # type: pd.DataFrame
    summary_per_function = summary_per_function.groupby(['function_name', "parameters"]).agg(aggregates)
    # TBD : add avg_automatic_time (avg time call for calls that ended automatically
    # TBD : add max_manual_time, median_manual_time??
    # TBD : filter per test scenario...

    summary_per_function = summary_per_function.rename(columns={
        "call_time": "avg_time",
        "manual_fixes_count": "manual_fixes_avg",
        "manual_fixes_time": "total_manual_time",
        "is_exception": "total_exceptions",
        "is_automatic": "automatic_success_ratio",
    })

    summary_per_function = summary_per_function["avg_time success_rate total_exceptions total_calls".split()]

    # summary_per_function["success_rate"] = summary_per_function.apply(axis=1)

    print "Summary for Connection Factory : {}".format(conn_factory_name)
    print "total runtime : ", stats[-1].end_time - stats[0].start_time
    if print_all:
        print all_calls_table

    print summary_per_function


def get_aggregates(additional_columns):
    aggregates = {
        "call_time": np.mean,
        "total_calls": np.sum,
        "manual_fixes_count": np.mean,
        "manual_fixes_time": np.sum,
        "is_exception": np.sum,
        "is_automatic": np.mean,
        "success_rate": np.mean,
    }
    additional_columns_set = set(chain.from_iterable(additional_columns))
    new_additional_columns = additional_columns_set.difference(aggregates)
    # atm every additional is summed. In the future if anyone needs add something else as well.
    for c in new_additional_columns:
        aggregates[c] = np.sum
    return aggregates


def main():
    start_time_string = time.strftime("%d_%H:%M:%S")

    with BetterTee(config.jointo.tmp_dir_path("run_conn_{}.log".format(start_time_string))):
        with indent_printing.time():
            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_connection_factories.keys(), True)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            conn_factory = all_connection_factories[factory_name]
            """@type: pydcomm.public.iconnection.ConnectionFactory"""

            test_scenario = get_complete_benchmark(repeats=3)

            runs = run_scenario(test_scenario, initial_context={'conn_factory': conn_factory})
            runs['conn_factory_name'] = conn_factory.__name__

            with open(config.jointo.tmp_dir_path("raw_data_{}.pickle".format(start_time_string)), "w") as f:
                cPickle.dump((conn_factory.__name__, runs), f)
                print_run_summary(runs['conn_factory_name'], runs['stats'], runs['params'], runs['ret_vals'],
                                  runs['additionals'],
                                  print_all=False)


def test_main():
    import mock
    import __builtin__

    # noinspection PyUnusedLocal
    @mock.patch.object(__builtin__, "open")
    @mock.patch.object(cPickle, "dump")
    @mock.patch.object(__builtin__, "raw_input")
    @mock.patch.object(time, "sleep")
    def call_main(msleep, mraw_input, mdump, mopen):
        msleep.return_value = None

        def dummy_raw_input(*values):
            i = [0]

            def inner(prompt):
                value = values[i[0]]
                i[0] += 1
                print prompt, value
                return value

            return inner

        mraw_input.side_effect = dummy_raw_input("dummy")

        main()

    call_main()


if __name__ == "__main__":
    main()
