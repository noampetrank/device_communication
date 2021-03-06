import socket
import subprocess

from pydcomm.general_android.connection.common import query_yes_no
from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix
from pydcomm.public.iconnection import ConnectingError
from pydcomm.general_android.connection.internal_adb_connection import InternalAdbConnection

PING_TIMEOUT = 100


def unreachable_device_fix(connection):
    """
    This fixer handles the scenario in which the device network was disconnected after the wireless ADB connection was
    created. In such case, the user is asked to reconnect to the network. In case of a successful reconnection by the
    user, the wireless ADB connection is restored.
    :type connection: InternalAdbConnection
    :param connection: The connection to fix
    """
    ip_address = connection.device_id.split(":")[0]

    # If device id is not an ip address then it's not a wireless connection, so there's no point in pinging.
    if not _is_valid_ip_address(ip_address):
        return

    initial_ping_succeed = _is_ping_successful(ip_address, PING_TIMEOUT)
    if initial_ping_succeed:
        print("Successfully pinged the device. This is not a disconnected network issue.")
        return

    last_ping_succeed = False
    while not last_ping_succeed:
        print("Device is not reachable.")
        print("Please reconnect the device to the network.")
        user_reconnected_device = query_yes_no("Did you reconnect the device?")
        if not user_reconnected_device:
            # The user didn't reconnect the device so there's nothing we can do here.
            return

        last_ping_succeed = _is_ping_successful(ip_address, PING_TIMEOUT)

    # If here, ping succeeded after the user reconnected the device to the network. Reconnect wireless ADB.
    try:
        print("Reconnecting to wireless ADB...")
        adb_connect_fix(connection)
        print("Reconnected successfully")
    except ConnectingError:
        print("Reconnection failed")


def _is_valid_ip_address(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False


def _is_ping_successful(ip_address, timeout):
    return subprocess.call(["ping", "-c", "1", ip_address], stdout=subprocess.PIPE) == 0
