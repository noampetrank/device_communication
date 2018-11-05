import logging
import time

import subprocess32 as subprocess

TEST_CONNECTION_ATTEMPTS = 10
ADB_CALL_MINIMAL_INTERVAL = 0.5


class DcommError(Exception):
    pass


class AdbConnectionError(DcommError):
    """ Error that happens when running adb() """

    # General error class for ADB connection
    def __init__(self, message=None, stderr=None, stdout=None, returncode=None):
        super(AdbConnectionError, self).__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class ConnectingError(DcommError):
    """Error that happens during the connection process"""
    pass

class ConnectionClosedError(DcommError):
    pass

class AdbConnection(object):
    def __init__(self, device_id=None):
        # TODO: test adb version
        self.log = logging.getLogger(__name__)

        # Initially set the last call to be "old" enough to allow the next call
        self.last_adb_call_time = time.time() - ADB_CALL_MINIMAL_INTERVAL

        if not device_id:
            self.device_id = self._get_device_to_connect()
            if not self.device_id:
                raise ConnectingError("No device given and no device choosing strategy used.")
        else:
            self.device_id = device_id
        self.log.info("Connected to device: \"{}\"".format(self.device_id))

    # noinspection PyMethodMayBeStatic
    def _get_device_to_connect(self):
        return ""

    def disconnect(self):
        """
        In wired connection does nothing
        """
        self.device_id = None

    def adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
        """
        Send the given command over adb.
        :type timeout: float | None
        :param timeout: ADB call timeout
        :type disable_fixers: bool
        :param disable_fixers: Whether to disable connection fixers when running this ADB command
        :type specific_device: bool
        :param specific_device: Whether the command is general or specific to the device connected by this connection
        :type command: str
        :param command: adb command (without "adb" in the beginning)
        :rtype: str
        :return: ADB command output
        :raises AdbConnectionError is case of a connection error
        :raises ValueError is case the command start with 'adb'
        :raises TimeoutExpired is case the ADB command was timed out
        """
        if specific_device and self.device_id is None:
            raise ConnectionClosedError()

        if specific_device and not disable_fixers:
            if not self.test_connection():
                raise AdbConnectionError("test_connection failed")

        if command.startswith("adb"):
            raise ValueError("Command should start with 'adb'")

        if specific_device:
            return self._run_adb_for_specific_device(command.split(), timeout)
        else:
            return self._run_adb_command(command.split(), timeout)

    def _run_adb_for_specific_device(self, params, timeout):
        """
        :type params: list[str]
        :param params: list of ADB params (split by spaces)
        :type timeout: float
        :param timeout: ADB call timeout
        :rtype: str
        :return: ADB command output
        :raises TimeoutExpired is case the ADB command was timed out
        """
        if self.device_id is None:
            raise ConnectionClosedError()
        return self._run_adb_command(["-s", self.device_id] + params, timeout=timeout)

    def _run_adb_command(self, params, timeout):
        """
        :type params: list[str]
        :param params: list of ADB params (split by spaces)
        :type timeout: float
        :param timeout: ADB call timeout
        :rtype: str
        :return: ADB command output
        :raises TimeoutExpired is case the ADB command was timed out
        :raises AdbConnectionError is case of ADB connection error
        """
        # Make sure enough time passed since the last ASB call
        time_since_last_adb_call = time.time() - self.last_adb_call_time
        if time_since_last_adb_call < ADB_CALL_MINIMAL_INTERVAL:
            time.sleep(ADB_CALL_MINIMAL_INTERVAL - time_since_last_adb_call)

        # Call ADB
        p = subprocess.Popen(["adb"] + params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, error = p.communicate(timeout=timeout)
        finally:
            self.last_adb_call_time = time.time()

        if p.returncode != 0:
            raise AdbConnectionError("adb returned with non-zero error code", stderr=error, returncode=p.returncode)
        return output.strip("\r\n")

    def test_connection(self):
        attempts = TEST_CONNECTION_ATTEMPTS
        while attempts > 0:
            try:
                attempts -= 1
                return self._run_adb_for_specific_device(["shell", "echo hi"], timeout=1) == "hi"
            except subprocess.TimeoutExpired:
                pass
            except AdbConnectionError as e:
                self.log.exception("Exception while connecting to wireless ADB:")
                self.log.exception(e)
            except ConnectionClosedError:
                raise
        return False
