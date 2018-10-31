import StringIO
import __builtin__
import sys
import unittest

import mock
from pydcomm.general_android.connection.fixers.computer_network_disconnected_fixes import network_disconnected_init, \
    network_disconnected_adb

from pydcomm.tests.helpers import TestCasePatcher


class NetworkDisconnectedFixerTests(unittest.TestCase):
    def setUp(self):
        self.patcher = TestCasePatcher(self)
        self.mock_netifaces = self.patcher.addPatch("pydcomm.general_android.connection.fixers.computer_network_disconnected_fixes.netifaces")

        self.mock_netifaces.interfaces.return_value = ["real", "lo", "virtual"]
        self.mock_netifaces.AF_INET = 2

        self.mock_netifaces.ifaddresses.side_effect = self.mock_ifaddresses
        self.interfaces = {}
        self.default_interface = {}

        self.connection = mock.Mock()
        self.connection.device_id = u"10.0.0.104"

    def mock_ifaddresses(self, device_name):
        if device_name == u"lo":
            return {2: [{'addr': u'127.0.0.1', 'netmask': u'255.0.0.0', 'peer': u'127.0.0.1'}],
                    10: [{'addr': u'::1',
                          'netmask': u'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'}],
                    17: [{'addr': u'00:00:00:00:00:00', 'peer': u'00:00:00:00:00:00'}]}
        if device_name in self.interfaces:
            return self.interfaces[device_name]
        return self.default_interface

    def test_network_disconnected_init__computer_not_connected_to_any_network__print_warning(self):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        capturedOutput = StringIO.StringIO()
        sys.stdout = capturedOutput

        network_disconnected_init(self.connection)

        sys.stdout = sys.__stdout__
        self.assertIn("Are you connected to a network?", capturedOutput.getvalue())

    def test_network_disconnected_init__computer_not_connected_to_correct_network__print_warning(self):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["real"] = {2: [{'addr': u'11.0.0.107',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["virtual"] = {2: [{'addr': u'172.17.0.1',
                                           'broadcast': u'172.17.255.255',
                                           'netmask': u'255.255.0.0'}],
                                      17: [{'addr': u'02:42:c1:c3:ef:67', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        capturedOutput = StringIO.StringIO()
        sys.stdout = capturedOutput

        network_disconnected_init(self.connection)

        sys.stdout = sys.__stdout__
        self.assertIn("Are you connected to a network?", capturedOutput.getvalue())

    def test_network_disconnected_init__computer_connected__correct_ip_is_saved(self):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["real"] = {2: [{'addr': u'10.0.0.107',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["virtual"] = {2: [{'addr': u'172.17.0.1',
                                           'broadcast': u'172.17.255.255',
                                           'netmask': u'255.255.0.0'}],
                                      17: [{'addr': u'02:42:c1:c3:ef:67', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}

        network_disconnected_init(self.connection)

        self.assertEqual(self.connection._initial_ip_address, {'addr': u'10.0.0.107',
                                                               'broadcast': u'10.0.0.255',
                                                               'netmask': u'255.255.255.0'})

    def test_network_disconnected_adb__computer_connected__no_text_shown_to_user(self):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["real"] = {2: [{'addr': u'10.0.0.107',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["virtual"] = {2: [{'addr': u'172.17.0.1',
                                           'broadcast': u'172.17.255.255',
                                           'netmask': u'255.255.0.0'}],
                                      17: [{'addr': u'02:42:c1:c3:ef:67', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        capturedOutput = StringIO.StringIO()
        sys.stdout = capturedOutput

        network_disconnected_init(self.connection)
        self.assertFalse(capturedOutput.getvalue())

        network_disconnected_adb(self.connection)

        sys.stdout = sys.__stdout__
        self.assertFalse(capturedOutput.getvalue())

    @mock.patch.object(__builtin__, 'raw_input')
    def test_network_disconnected_adb__computer_not_connected_to_any_network__user_is_prompted(self, mock_raw_input):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["real"] = {2: [{'addr': u'10.0.0.107',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["virtual"] = {2: [{'addr': u'172.17.0.1',
                                           'broadcast': u'172.17.255.255',
                                           'netmask': u'255.255.0.0'}],
                                      17: [{'addr': u'02:42:c1:c3:ef:67', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        capturedOutput = StringIO.StringIO()
        sys.stdout = capturedOutput

        network_disconnected_init(self.connection)
        self.assertFalse(capturedOutput.getvalue())
        self.interfaces = {}
        network_disconnected_adb(self.connection)
        mock_raw_input.assert_called()

    @mock.patch.object(__builtin__, 'raw_input')
    def test_network_disconnected_adb__computer_not_connected_to_correct_network__user_is_prompted(self, mock_raw_input):
        self.default_interface = {17: [{'addr': u'9c:5c:8e:97:41:21', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["real"] = {2: [{'addr': u'10.0.0.107',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        self.interfaces["virtual"] = {2: [{'addr': u'172.17.0.1',
                                           'broadcast': u'172.17.255.255',
                                           'netmask': u'255.255.0.0'}],
                                      17: [{'addr': u'02:42:c1:c3:ef:67', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        capturedOutput = StringIO.StringIO()
        sys.stdout = capturedOutput

        network_disconnected_init(self.connection)
        self.assertFalse(capturedOutput.getvalue())
        self.interfaces["real"] = {2: [{'addr': u'192.168.1.2',
                                        'broadcast': u'10.0.0.255',
                                        'netmask': u'255.255.255.0'}],
                                   10: [{'addr': u'fe80::9239:8b1:d415:39fe%enx000acd2b99a2',
                                         'netmask': u'ffff:ffff:ffff:ffff::/64'}],
                                   17: [{'addr': u'00:0a:cd:2b:99:a2', 'broadcast': u'ff:ff:ff:ff:ff:ff'}]}
        network_disconnected_adb(self.connection)
        mock_raw_input.assert_called()