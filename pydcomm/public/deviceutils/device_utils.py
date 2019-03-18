import re

from pydcomm.public.iconnection import IConnection


class DeviceUtils(object):
    def __init__(self, connection):
        """
        :param IConnection connection:
        """
        self.connection = connection

    def get_device_ip(self, verbose=True):
        """
        Get the ip address of the connected device.
        :return str|None: ip address
        """
        address = self.list_device_ips()
        if len(address) == 0:
            if verbose:
                print("Could not find ip address for the device. Please fix and try again")
            return None
        elif len(address) is 1:
            return address[0]
        else:
            if verbose:
                print("Found more than one ip address for the device. Please fix and try again")
            return None

    def list_device_ips(self):
        """
        List all the IPs of the device
        :rtype: List[str]
        """
        lines = self.connection.shell('ifconfig', timeout_ms=2000).splitlines()
        lines = [l for l in lines if 'inet addr' in l]
        return [re.split(" +", line)[2].replace('addr:', '') for line in lines if '127.0.0.1' not in line]
