import re
import subprocess


def parse_line(line):
    device_id, status = line.split("\t")
    # TODO: Ad unauthorized
    if "no permissions" in status or "unauthorized" in status:
        status = "no permissions"
    if re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4}\b", device_id):
        tpe = "wireless"
    else:
        tpe = "wired"
    return tpe, device_id, status.strip()


def adb_devices():
    output = subprocess.check_output(["adb", "devices"])
    if not output.startswith("List of devices attached"):
        raise Exception("Unexpected output from \"adb devices\"")
    return [parse_line(x) for x in output.splitlines()[1:] if x]


class WiredAdbConnection(object):
    def __init__(self):
        # TODO: test adb version
        self.device_id = self._get_device_to_connect()

    def _get_device_to_connect(self):
        return ""
