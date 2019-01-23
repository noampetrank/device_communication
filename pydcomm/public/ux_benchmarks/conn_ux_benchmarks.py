import cPickle
import string
import tempfile
import time

import numpy as np
from pybuga.infra.utils.buga_utils import indent_printing
from pybuga.infra.utils.user_input import UserInput
from pydcomm.public.connfactories import all_connection_factories
from pydcomm.public.iconnection import IConnection
from pydcomm.public.ux_benchmarks.rpc_ux_benchamrks import BetterTee
from pydcomm.public.ux_benchmarks.utils import run_scenario

_random_files = {}


def get_random_string(length):
    def _generate():
        return "".join(
            [string.ascii_letters[i] for i in np.random.randint(0, high=len(string.ascii_letters), size=length)])

    if length not in _random_files:
        _random_files[length] = _generate()
    return _random_files[length]


def single_api_call_summary(api_call, params=None, ret=None, additional=None, ignore_first_manual=True):
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
    import pandas as pd
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    all_calls_raw = [single_api_call_summary(call, p, ret, add) for call, p, ret, add in
                     zip(stats, params, ret_val, additionals)]

    all_calls_raw, additional_columns = zip(*all_calls_raw)

    all_calls_table = pd.DataFrame(list(all_calls_raw)).set_index(['function_name'])
    summary_per_function = pd.DataFrame(all_calls_table).assign(total_calls=lambda x: 1)

    aggregates = get_aggregates(additional_columns)
    summary_per_function = summary_per_function.groupby(['function_name', "parameters"]).agg(aggregates)
    # TBD : add avg_automatic_time (avg time call for calls that ended automatically
    # TBD : add max_manual_time, median_manual_time??
    # TBD : filter per test scenario...

    summary_per_function = summary_per_function.rename({"call_time": "avg_time",
                                                        "manual_fixes_count": "manual_fixes_avg",
                                                        "manual_fixes_time": "total_manual_time",
                                                        "is_exception": "total_exceptions",
                                                        "is_automatic": "automatic_success_ratio"})

    print "Summary for Connection Factory : {}".format(conn_factory_name)
    print "total runtime : ", stats[-1].end_time - stats[0].start_time
    if print_all:
        print all_calls_table

    print summary_per_function


def get_aggregates(additional_columns):
    aggregates = {"call_time": np.mean,
                  "total_calls": np.sum,
                  "manual_fixes_count": np.mean,
                  "manual_fixes_time": np.sum,
                  "is_exception": np.sum,
                  "is_automatic": np.mean}
    for c in additional_columns:
        if not additional_columns:
            continue
        for b in c:
            # atm every additional is summed. In the future if anyone needs add something else as well.
            aggregates[b] = np.sum
    return aggregates


class ConnectionAction(object):
    @staticmethod
    def CHOOSE_DEVICE_ID():
        def execute(scenario):
            device_id = scenario.context["conn_factory"].choose_device_id()
            return None, device_id, dict(device_id=device_id), {}

        return execute

    @staticmethod
    def CREATE_CONNECTION(device_id=None, **kwargs):
        def execute(scenario):
            """:type scenario: Scenario"""
            my_device_id = device_id if device_id is not None else scenario.context.get("device_id")
            connection = scenario.context["conn_factory"].create_connection(device_id=my_device_id, **kwargs)
            return (my_device_id,), None, dict(connection=connection), {}

        return execute

    @staticmethod
    def PUSH_PULL_RANDOM(length):
        """
        Create random file of size length, sends it, pulls it back, and then compares the files.
        :param length:
        :return:
        """
        random_string = get_random_string(length)

        def execute(scenario):
            """:type scenario: Scenario"""
            conn = scenario.context["connection"]
            remote_file_path = "/data/local/tmp/benchmark_test_file"
            with tempfile.NamedTemporaryFile() as tmp_push_file:
                tmp_push_file.file.write(random_string)
                tmp_push_file.file.close()
                conn.push(tmp_push_file.name, remote_file_path)
            with tempfile.NamedTemporaryFile() as tmp_pull_file:
                conn.pull(remote_file_path, tmp_pull_file.name)
                with open(tmp_pull_file.name) as pull:
                    pulled_data = pull.read()
                    success = pulled_data == random_string
            return (length,), None, {}, dict(recv_data_size=len(pulled_data), was_file_valid=success)

        return execute

    @staticmethod
    def SHELL_ECHO(length, sleep, timeout_ms=None):
        if length > 1024 * 1024:
            raise ValueError("Maximum echo is 1MB")  # Actually may be more, but not much more
        random_string = get_random_string(length)

        def execute(scenario):
            """:type scenario: Scenario"""
            conn = scenario.context["connection"]  # type: IConnection
            ret = conn.shell('echo "{}"'.format(random_string), timeout_ms=timeout_ms)
            success = ret.strip() == random_string.strip()
            time.sleep(sleep)
            return (length, sleep), len(ret), {}, dict(success=success)

        return execute

    @staticmethod
    def ROOT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].root()
            return (), None, {}, {}

        return execute

    @staticmethod
    def REMOUNT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].remount()
            return (), None, {}, {}

        return execute

    @staticmethod
    def INSTALL_UNINSTALL_DUMMYAPK():
        def execute(scenario):
            """:type scenario: Scenario"""
            # TODO: later

        return execute

    @staticmethod
    def DEVICE_ID():
        def execute(scenario):
            """:type scenario: Scenario"""
            device_name = scenario.context["connection"].device_name()
            return (), device_name, {}, {}

        return execute

    @staticmethod
    def DISCONNECT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].disconnect()
            return (), None, {}, {}

        return execute


def get_push_pull_scenario(rep_num=3, create_connections_num=10, input_lengths=(1, 1000, 1e5, 1e6, 1e7)):
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    for _ in range(rep_num):
        for _ in range(create_connections_num):
            scenario += [ConnectionAction.CREATE_CONNECTION()]
            scenario += [ConnectionAction.PUSH_PULL_RANDOM(int(l)) for l in input_lengths]
    scenario += [ConnectionAction.DISCONNECT()]
    return scenario


def get_repeating_scenario(rep_num, num_connection_check, check_interval, action, params):
    scenario = []
    for i in range(rep_num):
        scenario += [ConnectionAction.CREATE_CONNECTION()]
        for j in range(num_connection_check):
            scenario += [action(*params)]
            # TODO Add sleep here?
            # I don't remember why, there was a reason that I didn't add a sleep action. Maybe because I didn't want
            # it to appear in the table?
        scenario += [ConnectionAction.DISCONNECT()]


def get_echo_scenario(rep_num=3, num_connection_check=10, check_interval=0, echo_length=10):
    scenario = []
    for _ in range(rep_num):
        scenario += [ConnectionAction.CREATE_CONNECTION()]
        for _ in range(num_connection_check):
            scenario += [ConnectionAction.SHELL_ECHO(echo_length, check_interval)]
    return scenario


def get_old_benchmark_scenario():
    # This is how the old benchmark ran
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += get_echo_scenario(20, 5, 0)
    scenario += get_echo_scenario(7, 2, 20)
    scenario += get_echo_scenario(20, 1, 1)
    scenario += get_echo_scenario(20, 5, 0)
    scenario += get_echo_scenario(7, 2, 20)
    scenario += get_echo_scenario(20, 1, 1)
    return scenario


def get_short_benchmark_scenario():
    # This is how the old benchmark ran
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += get_echo_scenario(10, 1, 0)
    scenario += get_echo_scenario(5, 3, 0)
    return scenario


def get_big_messages_scenario(rep_num=1):
    return get_push_pull_scenario(rep_num, create_connections_num=1, input_lengths=[1e5] * 3)


def main():
    start_time_string = time.strftime("%H:%M:%S")

    with BetterTee("run_conn_{}.log".format(start_time_string)):
        with indent_printing.time():
            print "Choose connection factory for benchmark:"
            factory_name = UserInput.menu(all_connection_factories.keys(), True)
            if factory_name is None:
                print "Thanks, goodbye!"
                return

            conn_factory = all_connection_factories[factory_name]
            """@type: pydcomm.public.iconnection.ConnectionFactory"""

            test_scenario = get_big_messages_scenario(1)

            runs = run_scenario(test_scenario, initial_context={'conn_factory': conn_factory})
            runs['conn_factory_name'] = conn_factory.__name__

            with open("raw_data_" + start_time_string + ".pickle", "w") as f:
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
