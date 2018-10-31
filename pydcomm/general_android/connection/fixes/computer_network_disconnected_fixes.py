import ipaddress
import netifaces as netifaces


def is_ip_in_ips_network(unknown_ip, my_ip, my_subnet):
    return ipaddress.ip_address(unknown_ip) in ipaddress.ip_network(my_ip + u"/" + my_subnet, strict=False)


def network_disconnected_init(connection):
    # Save computer's original ip and subnet mask
    interfaces_and_addresses = get_connected_interfaces_and_addresses()
    for iface, addresses in interfaces_and_addresses:
        for address in addresses:
            if is_ip_in_ips_network(connection.device_id, address["addr"], address["netmask"]):
                connection._initial_ip_address = address
                return
    else:
        # Will happen only in the extreme case that after you connected to the device and before this fixer is run you are disconnected from the network
        print("Are you connected to a network?")


def network_disconnected_adb(connection):
    # if no IP - write that you are not connected
    # if IP, compare with original ip, if different, check that same subnet as device
    interfaces_and_addresses = get_connected_interfaces_and_addresses()
    for iface, addresses in interfaces_and_addresses:
        if any([addr["addr"] == connection._initial_ip_address["addr"] for addr in addresses]):
            # All is good, we are connected to the same network.
            return
        if any([is_ip_in_ips_network(connection.device_id, addr["addr"], addr["netmask"])
                for addr in addresses]):
            # We don't have the same ip, but we are still connected to the same network
            return
    print("Your computer is no longer connected to the network")
    print("Check that you are still on the correct wifi")
    raw_input()


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