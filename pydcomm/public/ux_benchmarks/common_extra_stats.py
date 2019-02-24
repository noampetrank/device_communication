import socket
import subprocess


def _get_pc_ip():
    # https://stackoverflow.com/a/28950776/857731
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = None
    finally:
        s.close()
    return ip


def _get_pc_wifi():
    try:
        return subprocess.check_output("iwgetid -r".split())
    except:
        return None


class CommonExtraStats(object):
    def __init__(self):
        pass  # PyCharm happiness

    # noinspection PyMethodMayBeStatic
    def __extra_stats__(self):
        return dict(
            hostname=socket.gethostname(),
            pc_ip=_get_pc_ip(),
            pc_wifi=_get_pc_wifi(),
        )
