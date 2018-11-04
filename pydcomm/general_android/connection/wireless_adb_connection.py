import re

from pydcomm.general_android.connection.fixers.computer_network_disconnected_fixes import \
    get_connected_interfaces_and_addresses, is_ip_in_ips_network
from pydcomm.general_android.connection.decorator_helpers import add_init_decorator
from pydcomm.general_android.connection.wired_adb_connection import ConnectingError, AdbConnectionError

ADB_TCP_PORT = 5555
CONNECTION_ATTEMPTS = 10


def get_device_ip(connection):
    """
    get the ip address of the connected device.
    :return: ip. None if device is not connected to wifi
    """
    ifconfig = connection.adb("shell ifconfig", disable_fixers=True)
    ips = re.findall(r"wlan0.*\n.*inet addr:(\d+\.\d+\.\d+\.\d+)", ifconfig)
    if ips:
        return unicode(ips[0])
    else:
        return None


def _run_adb_with_exception(connection, command, exception_message):
    try:
        connection.adb(command)
    except AdbConnectionError:
        raise ConnectingError(exception_message)


def connect_to_wireless_adb(connection, exception_message):
    # First, try disconnecting from previous wireless ADB to completely shut down any current connection
    try:
        connection.adb("disconnect " + connection.device_id, specific_device=False, disable_fixers=True)
    except AdbConnectionError:
        pass  # Disconnection will fail if a current connection doesn't exist, so we're ok with it.

    attempts = CONNECTION_ATTEMPTS
    connected = False
    while not connected and attempts > 0:
        try:
            output = connection.adb("connect " + connection.device_id, specific_device=False, disable_fixers=True)
            if "connected to " + connection.device_id in output:
                connected = True
                break
        except AdbConnectionError:
            pass # We can still retry
        attempts -= 1

    if not connected:
        raise ConnectingError(exception_message)


def connect_wireless(self, device_id=None):
    """
    This is a decorator over WiredAdbConnection, it adds a connection to wireless after the regular connection has been established.
    It is transformed later into a decorator called `add_connect_wireless`.
    :param self: AdbConnection
    :param device_id: ignored
    """
    # TODO: maybe append :5555 if needed

    if not self.test_connection():
        raise ConnectingError("No device connected to PC")

    device_on_same_network = False
    ip = None
    while not device_on_same_network:
        ip = get_device_ip(self)
        if not ip:
            raise ConnectingError("Device is not connected to wifi")
        interfaces = get_connected_interfaces_and_addresses()
        for iface_name, addresses in interfaces:
            if any([is_ip_in_ips_network(ip, addr["addr"], addr["netmask"]) for addr in addresses]):
                device_on_same_network = True
        if not device_on_same_network:
            print("Device is not connected to the same network as the computer, please change and press enter")
            raw_input()

    _run_adb_with_exception(self, "tcpip " + str(ADB_TCP_PORT), "Failed to change to tcp mode")

    self.device_serial = self.device_id
    self.device_id = ip + ":" + str(ADB_TCP_PORT)

    # TODO: Possibly need to change to mtp mode
    connect_to_wireless_adb(self, "Can't connect to ip {}".format(self.device_id))
    print("Device is connected over wifi, disconnect and press enter to continue.")
    # TODO: This needs to be in a fixer.
    # raw_input()
    # _run_with_exception("adb connect {}:5555".format(self.device_id).split(" "), "Can't connect to ip {}".format(self.device_id))


add_connect_wireless = add_init_decorator(connect_wireless, "connect_wireless")
