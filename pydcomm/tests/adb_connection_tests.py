from unittest import TestCase
from general_android.adb_connection import AdbConnectionFactory, MultiDeviceBehavior




# All tests are done with subprocess.check_output/Popen mocked to assert the output
class ConnectionFactoryUnitTests(TestCase):
    def setUp(self):
        self.cf = AdbConnectionFactory()

    def rooted_connection__connect__root_will_be_executed(self):
        con = self.cf.get_rooted_wireless_automated_connection()
        # Assert that calls to __init__ will also execute "adb root"

    def rooted_connection__phone_has_no_root__exception_pops(self):
        # mock to fail with no root message
        con = self.cf.get_rooted_wireless_automated_connection()
        # Assert correct exception

    def automated_recovery__adb_fails__adb_connect_is_done_again(self):
        con = self.cf.get_rooted_wireless_automated_connection()
        # mock so this call fails
        con.adb("something")
        # assert that "adb connect" is called

    def interactive_recovery__adb_fails__automated_calls_happen_before_interactive(self):
        con = self.cf.get_rooted_wireless_interactive_connection()
        # mock so this call fails
        con.adb("something")
        # assert that "adb connect" is called before anything is displayed to the user

    def interactive_recovery__adb_fails__interactive_happens(self):
        con = self.cf.get_rooted_wireless_interactive_connection()
        # mock so this call fails
        con.adb("something")
        # assert that something is displayed to the user

    def interactive_choose_device__one_device_conected__does_not_ask_user(self):
        con = self.cf.get_connection(multi_device=MultiDeviceBehavior.CHOOSE_FIRST)
        # Assert that connection was created and no message was displayed to the user

    def interactive_choose_device__multiple_devices_conected__asks_user_to_choose_and_connects(self):
        con = self.cf.get_connection(multi_device=MultiDeviceBehavior.CHOOSE_FIRST)
        # Assert that connection was created and no message was displayed to the user

    def choose_first_device__one_device__connects(self):
        pass

    def choose_first_device__multi_device__connects(self):
        # assert that the first device is connected
        pass

    def get_rooted_wireless_automated_connection__returns_the_correct_connection(self):
        con = self.cf.get_rooted_wireless_automated_connection()
        # Assert that the correct decorators were added

    def get_rooted_wireless_interactive_connection__returns_the_correct_connection(self):
        con = self.cf.get_rooted_wireless_interactive_connection()
        # Assert that the correct decorators were added


class AutomatedRecoveryTests(TestCase):
    # Tests that verify the automated behaviors that were not decided yet
    pass


class InteractiveRecoveryTests(TestCase):
    # Tests that verify the interactive behaviors that were not decided yet
    pass


# Will be defined later when wired and wireless adb connections are specified better.
# Basically it will make sure that "adb connect" is being called and that an exception
# is raised when the connection fails.
class ConnectionTests(TestCase):
    pass
