import string
import tempfile
import time
from collections import namedtuple

import numpy as np
from pydcomm.public.iconnection import IConnection

_random_files = {}

ActionResult = namedtuple("ActionResult", "parameters result context additionals exception")


def get_random_string(length):
    def _generate():
        print("Creating file of size " + str(length))
        return "".join(
            [string.ascii_letters[i] for i in np.random.randint(0, high=len(string.ascii_letters), size=length)])

    if length not in _random_files:
        _random_files[length] = _generate()
    return _random_files[length]


# After writing this I discovered that uxrecorder also saves the exception. I
# am keeping this since to use the exception from uxrecorder you need to wrap
# any call to it in a try except anyway, and I already did the work of converting
# the functions to the new namedtuple.
# tldr: life sucks so we save the exception twice.
def with_catch(action_result_func, parameters):
    def with_catch(scenario):
        try:
            return action_result_func(scenario)
        except Exception as e:
            return ActionResult(parameters, None, {}, {}, e)

    return with_catch


class ConnectionAction(object):
    @staticmethod
    def CHOOSE_DEVICE_ID():
        """
        :rtype: Scenario -> ActionResult
        """

        def execute(scenario):
            device_id = scenario.context["conn_factory"].choose_device_id()
            return ActionResult(parameters=None, result=device_id, context=dict(device_id=device_id), additionals={},
                                exception=None)

        return with_catch(execute, ())

    @staticmethod
    def CREATE_CONNECTION(device_id=None, **kwargs):
        """

        :param device_id:
        :param kwargs:
        :return (Scenario) -> ActionResult:
        """
        def execute(scenario):
            """:type scenario: Scenario"""
            my_device_id = device_id if device_id is not None else scenario.context.get("device_id")
            connection = scenario.context["conn_factory"].create_connection(device_id=my_device_id, **kwargs)
            return ActionResult(parameters=(my_device_id,), result=None, context=dict(connection=connection),
                                additionals={}, exception=None)

        return with_catch(execute, (device_id,))

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
            return ActionResult(parameters=(length,), result=None, context={},
                                additionals=dict(recv_data_size=len(pulled_data), success=success), exception=None)

        return with_catch(execute, (length,))

    @staticmethod
    def SHELL_ECHO(length, sleep=0, timeout_ms=None):
        if length > 1024 * 1024:
            raise ValueError("Maximum echo is 1MB")  # Actually may be more, but not much more
        random_string = get_random_string(length)

        def execute(scenario):
            """:type scenario: Scenario"""
            conn = scenario.context["connection"]  # type: IConnection
            ret = conn.shell('echo "{}"'.format(random_string), timeout_ms=timeout_ms)
            success = ret.strip() == random_string.strip()
            time.sleep(sleep)
            return ActionResult(parameters=(length, sleep, timeout_ms), result=len(ret), context={},
                                additionals=dict(success=success), exception=None)

        return with_catch(execute, (length, sleep, timeout_ms))

    @staticmethod
    def ROOT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].root()
            return ActionResult(parameters=(), result=None, context={}, additionals={}, exception=None)

        return with_catch(execute, ())

    @staticmethod
    def REMOUNT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].remount()
            return ActionResult(parameters=(), result=None, context={}, additionals={}, exception=None)

        return with_catch(execute, ())

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
            return ActionResult(parameters=(), result=device_name, context={}, additionals={}, exception=None)

        return with_catch(execute, ())

    @staticmethod
    def DISCONNECT():
        def execute(scenario):
            """:type scenario: Scenario"""
            scenario.context["connection"].disconnect()
            return ActionResult(parameters=(), result=None, context={}, additionals={}, exception=None)

        return with_catch(execute, ())
