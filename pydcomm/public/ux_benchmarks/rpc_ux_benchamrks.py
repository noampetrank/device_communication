import pickle
import time
import sys
from random import randint
from collections import namedtuple

import numpy as np
from pybuga.tests.utils.test_helpers import Tee
from pybuga.infra.utils.user_input import UserInput
from pydcomm.rpc.bugarpc import all_rpc_factories, all_rpc_test_so

from pydcomm.utils.userexpstats import ApiCallsRecorder


ApiAction = namedtuple("ApiAction", "function_name params")


def single_api_call_summary(api_call, params=None, ret=None, ignore_first_manual=True):
    res = {
        "function_name":        api_call.function_name,
        "call_time":            api_call.end_timme - api_call.start_time,
        "manual_fixes_count":   len(api_call.manual_times),
        "manual_fixes_time":    sum([end-start for start, end in api_call.manual_times[ignore_first_manual:]]),
        "is_exception":         api_call.is_exception,
        "is_automatic":         len(api_call.manual_times) == 0,
        "is_success": not api_call.is_exception
    }

    if api_call.function_name == "call" and params is not None:
        res['data_size'] = len(params[1])
        if ret is not None:
            res['corrupted_data'] = np.any(np.array(map(ord, params[1])) + 1 != ret)
            res['recv_data_size'] = len(ret)

    return res


def print_run_summary(rpc_factory_name, stats, params, ret_val, print_all=False):
    import pandas
    all_calls_raw = [single_api_call_summary(call, p, ret) for call, p, ret in zip(stats, params, ret_val)]

    all_calls_table = pandas.DataFrame(all_calls_raw).set_index(['function_name'])

    summary_per_function = pandas.DataFrame(all_calls_table).assign(total_calls=lambda x: 1)
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


class RPCDummyAction(object):
    @staticmethod
    def INSTALL():
        return ApiAction(function_name="install", params=())

    @staticmethod
    def INIT():
        return ApiAction(function_name="__init__", params=())

    @staticmethod
    def CALL_DUMMY_SEND(length):
        random_string = "".join(chr(randint(0, 256)) for _ in range(length))
        return ApiAction(function_name="call", params=["dummy_send", random_string])

    @staticmethod
    def CREATE_CONNECTION(rpc_id=29999):
        return ApiAction(function_name="create_connection", params=[rpc_id])


def run_scenario(actions, so_path, rpc_factory):  # TBD flag for only parameters lengths?
    ret_vals = []
    params = [api_action.params for api_action in actions]
    factory = None
    recorder = ApiCallsRecorder()

    with recorder:
        try:
            for api_action in actions:
                if api_action.function_name == "install":
                    rpc_factory.install(so_path)
                if api_action.function_name == "__init__":
                    factory = rpc_factory()
                    ret_vals.append(factory)
                elif api_action.function_name == "create_connection":
                    factory.create_connection(*api_action.params)
                elif api_action.function_name == "call":
                    factory.call(*api_action.params)
        except KeyboardInterrupt:
            pass
    return {"stats": recorder.api_stats, "params": params, "ret_vals": ret_vals}


# TODO: Extract code from pybuga to someplace else
class BetterTee(Tee):
    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout


def get_basic_scenario(rep_num=3, create_connections_num=10, input_lengths=(1, 1000, 1e5, 1e6, 1e7)):
    scenario = []
    for _ in range(rep_num):
        scenario += [RPCDummyAction.INSTALL(), RPCDummyAction.INIT()]
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
    test_scenario = get_basic_scenario()  # TBD choose from menu? add repr string?
    from pybuga.infra.utils.buga_utils import indent_printing
    start_time_string = time.strftime("%H:%M:%S")
    with BetterTee("run_{}.log".format(start_time_string)):
        with indent_printing.time():

            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_rpc_factories.keys(), False)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            rpc_factory_cls = all_rpc_factories[factory_name]  # TBD
            rpc_test_so = all_rpc_test_so[factory_name]  # TBD
            # TBD
            # The test .so should have a dummy excecuter with port 29999 and one method:
            # dummy_send(string input) which returns the string input + 1 (each character is increased by 1 modulu 256)

            runs = run_scenario(test_scenario, rpc_test_so, rpc_factory_cls)
            runs['rpc_factory_name'] = rpc_factory_cls.__name__
            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
                pickle.dump((rpc_factory_cls.__name__, runs), f)
                print_run_summary(runs['rpc_factory_name'], runs['stats'], runs['params'], runs['ret_val'],
                                  print_all=False)


def test_main():
    import mock
    import __builtin__

    @mock.patch.object(__builtin__, "raw_input")
    @mock.patch.object(time, "sleep")
    def call_main(msleep, mraw_input):
        msleep.return_value = None
        mraw_input.side_effect = ["dummy", "wired"]
        main()

    call_main()


if __name__ == "__main__":
    main()
