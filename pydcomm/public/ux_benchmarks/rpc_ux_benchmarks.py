import cPickle
import time
import sys
from collections import namedtuple

import numpy as np
from mock import MagicMock
from pybuga.tests.utils.test_helpers import Tee
from pybuga.infra.utils.user_input import UserInput
from pydcomm.public.rpcfactories import all_rpc_factories

from pydcomm.public.ux_stats import ApiCallsRecorder


ApiAction = namedtuple("ApiAction", "function_name params")


def single_api_call_summary(api_call, params=None, ret=None, ignore_first_manual=True):
    res = {
        "function_name":        api_call.function_name,
        "call_time":            api_call.end_time - api_call.start_time,
        "manual_fixes_count":   len(api_call.manual_times),
        "manual_fixes_time":    sum([end-start for start, end in api_call.manual_times[ignore_first_manual:]]),
        "is_exception":         api_call.is_exception,
        "is_automatic":         len(api_call.manual_times) == 0,
        "corrupted_data":       False
    }

    if api_call.function_name == "call" and params is not None:
        res['send_data_size'] = len(params[1])
        if ret is not None:
            res['corrupted_data'] = (np.frombuffer(params[1], np.uint8) + 1).tostring() != ret
            res['recv_data_size'] = len(ret)

    res["is_success"] = not api_call.is_exception and not res["corrupted_data"]

    return res


def print_run_summary(rpc_factory_name, stats, params, ret_val, print_all=False):
    import pandas as pd
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    all_calls_raw = [single_api_call_summary(call, p, ret) for call, p, ret in zip(stats, params, ret_val)]

    all_calls_table = pd.DataFrame(all_calls_raw).set_index(['function_name'])
    all_calls_table.fillna(value=0, inplace=True)

    summary_per_function = pd.DataFrame(all_calls_table).assign(total_calls=lambda x: 1)
    summary_per_function = summary_per_function.groupby(['function_name', "send_data_size", "recv_data_size"]).\
        agg({"call_time": np.mean,
             "total_calls": np.sum,
             "manual_fixes_count": np.mean,
             "manual_fixes_time": np.sum,
             "is_exception": np.sum,
             "is_automatic": np.mean,
             "is_success": np.mean,
             "corrupted_data": np.sum})
    # TBD : add avg_automatic_time (avg time call for calls that ended automatically
    # TBD : add max_manual_time, median_manual_time??
    # TBD : filter per test scenario...

    summary_per_function = summary_per_function.rename({"call_time": "avg_time",
                                                        "manual_fixes_count": "manual_fixes_avg",
                                                        "manual_fixes_time": "total_manual_time",
                                                        "is_exception": "total_exceptions",
                                                        "is_automatic": "automatic_success_ratio",
                                                        "is_success": "success_ratio",
                                                        "corrupted_data": "total_corrupted_data"})

    print "Summary for RPC Factory : {}".format(rpc_factory_name)
    print "total runtime : ", stats[-1].end_time - stats[0].start_time
    if print_all:
        print all_calls_table

    print summary_per_function


class Scenario(object):
    def __init__(self, stats, params, ret_vals, uxrecorder, connection, so_path, rpc_factory):
        self.stats = stats
        self.params = params
        self.ret_vals = ret_vals
        self.uxrecorder = uxrecorder
        self.connection = connection
        self.so_path = so_path
        self.rpc_factory = rpc_factory
        self.context = {}


class RPCDummyAction(object):
    RPC_ID = 29999

    @staticmethod
    def CHOOSE_DEVICE_ID():
        def execute(scenario):
            scenario.params.append(())
            scenario.context['device_id'] = device_id = scenario.rpc_factory.choose_device_id()
            scenario.ret_vals.append(device_id)
            scenario.stats.append(scenario.uxrecorder.api_stats[-1])
        return execute

    @staticmethod
    def INSTALL(rpc_id=None):
        rpc_id = rpc_id or RPCDummyAction.RPC_ID

        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.params.append(())
            scenario.ret_vals.append(scenario.rpc_factory.install_executor(scenario.so_path, rpc_id,
                                                                           scenario.context.get('device_id')))
            scenario.stats.append(scenario.uxrecorder.api_stats[-1])
        return execute

    @staticmethod
    def CALL_DUMMY_SEND(length):
        random_string = np.random.randint(0, 256, int(length), np.uint8).tostring()

        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.params.append(("dummy_send", random_string))
            scenario.ret_vals.append(scenario.connection.call("dummy_send", random_string))
            scenario.stats.append(scenario.uxrecorder.api_stats[-1])

        return execute

    @staticmethod
    def CREATE_CONNECTION(rpc_id=None):
        rpc_id = rpc_id or RPCDummyAction.RPC_ID

        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.params.append((rpc_id,))
            scenario.connection = scenario.rpc_factory.create_connection(rpc_id,
                                                                         device_id=scenario.context.get('device_id'))
            scenario.ret_vals.append(None)
            scenario.stats.append(scenario.uxrecorder.api_stats[-1])
        return execute


def run_scenario(actions, so_path, rpc_factory):  # TBD flag for only parameters lengths?
    """

    :param list[(scenario)->None] actions: Action to run.
    :param str so_path: Path to test so relative to test-files repository.
    :param pydcomm.public.bugarpc.IRemoteProcedureClientFactory rpc_factory: Caller factory to use.
    :return: Results of run.
    :rtype: dict
    """
    uxrecorder = ApiCallsRecorder()
    scenario = Scenario([], [], [], uxrecorder, None, so_path, rpc_factory)

    with uxrecorder:
        try:
            for api_action in actions:
                api_action(scenario)
        except KeyboardInterrupt:
            pass
    return dict(stats=scenario.stats, params=scenario.params, ret_vals=scenario.ret_vals)


# TODO: Extract code from pybuga to someplace else
class BetterTee(Tee):
    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout


def get_basic_scenario(rep_num=3, create_connections_num=10, input_lengths=(1, 1000, 1e5, 1e6, 1e7)):
    scenario = [RPCDummyAction.CHOOSE_DEVICE_ID()]
    for _ in range(rep_num):
        scenario += [RPCDummyAction.INSTALL()]
        for _ in range(create_connections_num):
            scenario += [RPCDummyAction.CREATE_CONNECTION()]
            scenario += [RPCDummyAction.CALL_DUMMY_SEND(l) for l in input_lengths]
    return scenario


def get_multiple_connection_scenario():
    return get_basic_scenario(1, create_connections_num=10, input_lengths=[]) + [RPCDummyAction.CALL_DUMMY_SEND(10000)]


def get_small_msgs_scenario(rep_num=1):
    return get_basic_scenario(rep_num, create_connections_num=10, input_lengths=[10] * 100)


def get_long_connection_scenario(rep_num=1):
    return get_basic_scenario(rep_num, create_connections_num=1, input_lengths=[1e6] * 1000)


def get_scenario_similar_to_recording_script():
    pass
    # TBD


def main():
    from pybuga.infra.utils.buga_utils import indent_printing
    start_time_string = time.strftime("%H:%M:%S")

    with BetterTee("run_rpc_{}.log".format(start_time_string)):
        with indent_printing.time():
            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_rpc_factories.keys(), False)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            pair = all_rpc_factories[factory_name]
            rpc_factory_cls = pair.factory_cls
            """@type: pydcomm.public.bugarpc.ICallerFactory"""
            rpc_test_so = pair.test_so

            test_scenario = get_basic_scenario()
            runs = run_scenario(test_scenario, rpc_test_so, rpc_factory_cls)
            runs['rpc_factory_name'] = rpc_factory_cls.__name__

            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
                cPickle.dump((rpc_factory_cls.__name__, runs), f)
                print_run_summary(runs['rpc_factory_name'], runs['stats'], runs['params'], runs['ret_vals'],
                                  print_all=False)


def test_main():
    import mock
    import __builtin__

    # noinspection PyUnusedLocal
    @mock.patch.object(__builtin__, "open")
    @mock.patch.object(cPickle, "dump")
    @mock.patch.object(__builtin__, "raw_input")
    @mock.patch.object(time, "sleep")
    @mock.patch("pydcomm.public.ux_benchmarks.rpc_ux_benchmarks.ApiCallsRecorder._get_save_file", return_value=MagicMock())
    def call_main(m_get_save_file, msleep, mraw_input, mdump, mopen):
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
