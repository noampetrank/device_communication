import cPickle
import time
import sys
from collections import namedtuple

import numpy as np
from pybuga.tests.utils.test_helpers import Tee
from pybuga.infra.utils.user_input import UserInput
from pydcomm.public.connfactories import all_connection_factories

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


def print_run_summary(conn_factory_name, stats, params, ret_val, print_all=False):
    import pandas as pd
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    all_calls_raw = [single_api_call_summary(call, p, ret) for call, p, ret in zip(stats, params, ret_val)]

    all_calls_table = pd.DataFrame(all_calls_raw).set_index(['function_name'])

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

    print "Summary for Connection Factory : {}".format(conn_factory_name)
    print "total runtime : ", stats[-1].end_time - stats[0].start_time
    if print_all:
        print all_calls_table

    print summary_per_function


class Scenario(object):
    def __init__(self, stats, params, ret_vals, uxrecorder, connection, conn_factory):
        self.stats = stats
        """@type: list[pydcomm.public.ux_stats.ApiCall]"""

        self.params = params
        """@type: list[dict]"""

        self.ret_vals = ret_vals
        """@type: list"""

        self.uxrecorder = uxrecorder
        """@type: ApiCallsRecorder"""

        self.connection = connection
        """@type: pydcomm.public.iconnection.IConnection"""

        self.conn_factory = conn_factory
        """@type: pydcomm.public.iconnection.ConnectionFactory"""


class ConnectionAction(object):
    @staticmethod
    def CREATE_CONNECTION(device_id=None, **kwargs):
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def PUSH(local_path, path_on_device):
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def PUSH_PULL_RANDOM(length):
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def PULL(path_on_device, local_path):
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def SHELL(command, timeout_ms=None):
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def ROOT():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def REMOUNT():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def INSTALL():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def UNINSTALL():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def DEVICE_ID():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute

    @staticmethod
    def DISCONNECT():
        def execute(scenario):
            """:type scenario: Scenario"""

        return execute


def run_scenario(actions, conn_factory):
    """

    :param list[(scenario)->None] actions: Action to run.
    :param pydcomm.public.iconnection.ConnectionFactory conn_factory: Caller factory to use.
    :return: Results of run.
    :rtype: dict
    """
    uxrecorder = ApiCallsRecorder()
    scenario = Scenario([], [], [], uxrecorder, None, conn_factory)

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
    scenario = []
    for _ in range(rep_num):
        for _ in range(create_connections_num):
            scenario += [ConnectionAction.CREATE_CONNECTION()]
            scenario += [ConnectionAction.PUSH_PULL_RANDOM(l) for l in input_lengths]
    return scenario


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

    with BetterTee("run_conn_{}.log".format(start_time_string)):
        with indent_printing.time():
            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_connection_factories.keys(), False)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            conn_factory = all_connection_factories[factory_name]
            """@type: pydcomm.public.iconnection.ConnectionFactory"""

            test_scenario = get_basic_scenario()

            runs = run_scenario(test_scenario, conn_factory)
            runs['conn_factory_name'] = conn_factory.__name__

            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
                cPickle.dump((conn_factory.__name__, runs), f)
                print_run_summary(runs['conn_factory_name'], runs['stats'], runs['params'], runs['ret_vals'],
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
