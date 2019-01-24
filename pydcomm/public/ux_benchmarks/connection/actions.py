import string
import tempfile
import time

import numpy as np
from pydcomm.public.iconnection import IConnection

_random_files = {}


def get_random_string(length):
    def _generate():
        return "".join(
            [string.ascii_letters[i] for i in np.random.randint(0, high=len(string.ascii_letters), size=length)])

    if length not in _random_files:
        _random_files[length] = _generate()
    return _random_files[length]


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
            return (length,), None, {}, dict(recv_data_size=len(pulled_data), success=success)

        return execute

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
