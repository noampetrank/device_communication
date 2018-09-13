import logging
import subprocess


class AdbConnectionError(Exception):
    # General error class for ADB connection
    def __init__(self, *args, **kwargs):
        self.stderr = None
        self.stdout = None
        self.returncode = None
        super(AdbConnectionError, self).__init__(*args, **kwargs)


class WiredAdbConnection(object):
    def __init__(self, device_id=None):
        # TODO: test adb version
        if not device_id:
            self.device_id = self._get_device_to_connect()
            if not self.device_id:
                raise ValueError("No device given and no device choosing strategy used.")
        else:
            self.device_id = device_id
        logging.info("Connected to device: \"{}\"".format(self.device_id))

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
        logging.info("adb params:", *params)

        if params[0] is "adb":
            logging.warn("adb() called with 'adb' as first parameter. Is this intentional?")

        p = subprocess.Popen(["adb", "-s", self.device_id] + list(params), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if p.returncode != 0:
            err = AdbConnectionError("adb returned with non-zero error code")
            err.stderr = error
            err.returncode = p.returncode
            raise err
        return output
