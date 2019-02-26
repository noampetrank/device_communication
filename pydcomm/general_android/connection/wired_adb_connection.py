import logging
import time
import os

import subprocess32 as subprocess

from pydcomm.public.iconnection import ConnectionClosedError, CommandFailedError, ConnectingError

TEST_CONNECTION_ATTEMPTS = 3
TEST_CONNECTION_TIMEOUT = 0.3
ADB_CALL_MINIMAL_INTERVAL = 0.5


class InternalAdbConnection(object):
    def __init__(self, device_id=None, filter_wireless_devices=False):
        # Print adb commands only if env variable is set
        self.debug = os.environ.has_key("BUGA_ADB_DEBUG")
        # TODO: test adb version
        self.log = logging.getLogger(__name__)

        # Initially set the last call to be "old" enough to allow the next call
        self.last_adb_call_time = time.time() - ADB_CALL_MINIMAL_INTERVAL

        self.wired = True

        if not device_id:
            self.device_id = self._get_device_to_connect(filter_wireless_devices)
            if not self.device_id:
                raise ConnectingError("No device given and no device choosing strategy used.")
        else:
            self.device_id = device_id

        if self.adb(["shell", "echo hi"], timeout=1).strip() != "hi":
            raise ConnectingError("Wired connection failed")

        self.log.info("Connected to device: \"{}\"".format(self.device_id))

    # noinspection PyMethodMayBeStatic
    def _get_device_to_connect(self, filter_wireless_devices=False):
        return ""

    def disconnect(self):
        """
        In wired connection does nothing
        """
        self.device_id = None

    def adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
        """
        Send the given command over adb.
        :param float | None timeout: ADB call timeout
        :param bool disable_fixers: Whether to disable connection fixers when running this ADB command
        :param bool specific_device: Whether the command is general or specific to the device connected by this connection
        :param str|list[str] command: adb command (without "adb" in the beginning)
        :return str: ADB command output
        :raises AdbConnectionError is case of a connection error
        :raises ValueError is case the command start with 'adb'
        :raises TimeoutExpired is case the ADB command was timed out
        """
        if type(command) is not list:
            command = command.split()

        if specific_device and self.device_id is None:
            raise ConnectionClosedError()
        if specific_device and not disable_fixers:
            if not self.test_connection():
                raise CommandFailedError("test_connection failed")
        if command[0] == "adb":
            raise ValueError("Command should not start with 'adb'")

        if specific_device:
            return self._run_adb_for_specific_device(command, timeout)
        else:
            return self._run_adb_command(command, timeout)

    def _run_adb_for_specific_device(self, params, timeout):
        """
        :param list[str] params: list of ADB params (split by spaces)
        :param float timeout: ADB call timeout
        :return str: ADB command output
        :raises TimeoutExpired is case the ADB command was timed out
        """
        if self.device_id is None:
            raise ConnectionClosedError()
        return self._run_adb_command(["-s", self.device_id] + params, timeout=timeout)

    def _run_adb_command(self, params, timeout):
        """
        :type params:
        :param list[str] params: list of ADB params (split by spaces)
        :param float timeout: ADB call timeout
        :return str: ADB command output
        :raises TimeoutExpired is case the ADB command was timed out
        :raises AdbConnectionError is case of ADB connection error
        """
        # Make sure enough time passed since the last ASB call
        time_since_last_adb_call = time.time() - self.last_adb_call_time
        if time_since_last_adb_call < ADB_CALL_MINIMAL_INTERVAL:
            time.sleep(ADB_CALL_MINIMAL_INTERVAL - time_since_last_adb_call)

        if self.debug: print(["adb"] + params)
        p = subprocess.Popen(["adb"] + params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, error = p.communicate(timeout=timeout)
        finally:
            self.last_adb_call_time = time.time()

        if p.returncode != 0:
            raise CommandFailedError("adb returned with non-zero error code",
                                     stdout=output, stderr=error, returncode=p.returncode)
        return output.strip("\r\n")

    def test_connection(self):
        attempts = TEST_CONNECTION_ATTEMPTS
        while attempts > 0:
            try:
                attempts -= 1
                return self._run_adb_for_specific_device(["shell", "echo hi"], timeout=TEST_CONNECTION_TIMEOUT) == "hi"
            except subprocess.TimeoutExpired:
                pass
            except CommandFailedError as e:
                pass
            except ConnectionClosedError:
                raise
        return False
