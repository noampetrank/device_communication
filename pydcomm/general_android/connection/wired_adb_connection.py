import logging


class WiredAdbConnection(object):
    def __init__(self, device_id=None):
        # TODO: test adb version
        if not device_id:
            self.device_id = self._get_device_to_connect()
            if not self.device_id:
                raise ValueError("No device given and no device choosing strategy used.")
        logging.info("Connected to device: \"{}\"".format(self.device_id))

    def _get_device_to_connect(self):
        return ""

    def adb(self, *params):
        pass
