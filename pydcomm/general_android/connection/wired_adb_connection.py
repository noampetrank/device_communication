import logging

import subprocess32 as subprocess
from subprocess32 import CalledProcessError


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


class AdbConnection(object):
    def __init__(self, device_id=None):
        # TODO: test adb version
        self.log = logging.getLogger(__name__)
        if not device_id:
            self.device_id = self._get_device_to_connect()
            if not self.device_id:
                raise ConnectingError("No device given and no device choosing strategy used.")
        else:
            self.device_id = device_id
        self.log.info("Connected to device: \"{}\"".format(self.device_id))

    def _get_device_to_connect(self):
        return ""

    def disconnect(self):
        """
        In wired connection does nothing
        """
        self.device_id = None
        pass

    def adb(self, *params):
        """
        Send the given command over adb.
        :type params: str
        :param params: array of split args to adb command
        :rtype: str
        :return: Adb command output
        :raises AdbConnectionError
        """
        if self.device_id is None:
            raise AdbConnectionError("This connection was closed")

        if not self.test_connection():
            raise AdbConnectionError("test_connection failed")
        self.log.info("adb params: %s", list(params))

        if params[0] is "adb":
            self.log.warn("adb() called with 'adb' as first parameter. Is this intentional?")
        return self._run_adb(params)

    def _run_adb(self, params):
        p = subprocess.Popen(["adb", "-s", self.device_id] + list(params), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if p.returncode != 0:
            raise AdbConnectionError("adb returned with non-zero error code", stderr=error, returncode=p.returncode)
        return output

    def test_connection(self):
        try:
            return subprocess.check_output(["adb", "-s", self.device_id, "shell", "echo hi"], timeout=1).strip() == "hi"
        except subprocess.TimeoutExpired:
            self.log.warn("test_connection timed out")
            return False
        except CalledProcessError as e:
            self.log.exception(e)
            return False
