import ipaddress
import netifaces as netifaces
import subprocess32 as subprocess


def add_rooted_impl(connection, device_id=None):
    connection.adb("root")
    connection.adb("remount")


# region Auto fixes

def restart_adb_server_fix(connection):
    connection.adb("kill-server", specific_device=False)
    connection.adb("start-server", specific_device=False)


def set_usb_mode_to_mtp_fix(connection):
    connection.adb("shell setprop sys.usb.config \"mtp,adb\"")


# endregion Auto fixes

# region Manual fixes




def get_connected_interfaces_and_addresses():
    """
    Returns connected network interfaces - non loopback and that have an IP address.
    Example output:
    ```
    [(u'enx000acd2b99a2',
      [{'addr': u'10.0.0.107',
        'broadcast': u'10.0.0.255',
        'netmask': u'255.255.255.0'}]),
     (u'docker0',
      [{'addr': u'172.17.0.1',
        'broadcast': u'172.17.255.255',
        'netmask': u'255.255.0.0'}])]
    ```

    :return: List of tuples of interface name and addresses
    :rtype: list[tuple[string, list[dict]]]
    """
    interfaces_and_addresses = [(x, netifaces.ifaddresses(x).get(netifaces.AF_INET)) for x in netifaces.interfaces()]
    interfaces_and_addresses = [x for x in interfaces_and_addresses if x[1] is not None and x[1][0]["addr"] != u"127.0.0.1"]
    return interfaces_and_addresses


def get_connected_interfaces_and_addresses():
    """
    Returns connected network interfaces - non loopback and that have an IP address.
    Example output:
    ```
    [(u'enx000acd2b99a2',
      [{'addr': u'10.0.0.107',
        'broadcast': u'10.0.0.255',
        'netmask': u'255.255.255.0'}]),
     (u'docker0',
      [{'addr': u'172.17.0.1',
        'broadcast': u'172.17.255.255',
        'netmask': u'255.255.0.0'}])]
    ```

    :return: List of tuples of interface name and addresses
    :rtype: list[tuple[string, list[dict]]]
    """
    interfaces_and_addresses = [(x, netifaces.ifaddresses(x).get(netifaces.AF_INET)) for x in netifaces.interfaces()]
    interfaces_and_addresses = [x for x in interfaces_and_addresses if x[1] is not None and x[1][0]["addr"] != u"127.0.0.1"]
    return interfaces_and_addresses

# endregion Manual fixes
