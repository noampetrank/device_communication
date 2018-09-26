import logging
import re

import subprocess32 as subprocess
from subprocess32 import CalledProcessError

from pydcomm.general_android.connection.decorator_helpers import add_init_decorator


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


def get_device_ip(device_id):
    """
    get the ip address of the connected device.
    :return: ip. None if device is not connected to wifi
    """
    ifconfig = subprocess.check_output('adb -s {} shell ifconfig'.format(device_id).split(" "))
    ips = re.findall(r"wlan0.*\n.*inet addr:(\d+\.\d+\.\d+\.\d+)", ifconfig)
    if ips:
        return ips[0]
    else:
        return None


def _run_with_exception(command, exception_message):
    try:
        subprocess.check_call(command)
    except CalledProcessError:
        raise ConnectingError(exception_message)


def connect_wireless(self, device_id=None):
    if not self.test_connection():
        raise ConnectingError("No device connected to PC")
    ip = get_device_ip(device_id or self.device_id)
    # TODO: Test that the ip is in the same subnet
    if not ip:
        raise ConnectingError("Device is not connected to wifi")
    else:
        self.device_serial = self.device_id
        self.device_id = ip
    # TODO: Possibly need to change to mtp mode
    _run_with_exception("adb tcpip 5555".split(" "), "Failed to change to tcp mode")
    _run_with_exception("adb connect {}:5555".format(self.device_id).split(" "), "Can't connect to ip {}".format(self.device_id))
    print("Device is connected over wifi, disconnect and press enter to continue.")
    # TODO: This needs to be in a fixer.
    # raw_input()
    # _run_with_exception("adb connect {}:5555".format(self.device_id).split(" "), "Can't connect to ip {}".format(self.device_id))


add_connect_wireless = add_init_decorator(connect_wireless, "connect_wireless")
