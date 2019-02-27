from traceback import print_exc

from python.infra.utils.user_input import UserInput

from pydcomm.public.iconnection import ConnectionClosedError


# def add_adb_recovery_decorator(fix_function):
#     def inner(connection):
#         old_adb = connection.adb
#
#         def new_adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
#             old_test_connection = self.test_connection
#             try:
#                 if not disable_fixers and specific_device:
#                     if not self.test_connection():
#                         try:
#                             fix_function(self)
#                         except Exception as e:
#                             self.log.warn("Fix {} failed ".format(fix_function.__name__), exc_info=e)
#                     else:
#                         self.test_connection = lambda: True
#                 return old_adb(self, command, timeout, specific_device, disable_fixers)
#             finally:
#                 self.test_connection = old_test_connection
#
#         connection.adb = new_adb
#         return connection
#
#     return inner


def add_fixers(connection_cls, method, fixers):
    """
    :param type connection_cls:
    :param str method:
    :param list[InternalAdbConnection -> None]:
    :return:
    """
    class TempClass(connection_cls):
        pass
    old_method = getattr(connection_cls, method)

    def run_with_fixers(*args, **kwargs):
        for fix in fixers:
            try:
                return old_method(*args, **kwargs)
            except ConnectionClosedError:
                if kwargs.get("disable_fixers",False):
                    raise
                try:
                    fix(args[0])
                except Exception:
                    print_exc()
                    # raise
        print("please call a developer.")
        while True:
            try:
                if not UserInput.yes_no("Do you want to try again? [y/n]"):
                    break
                return old_method(*args, **kwargs)
            except ConnectionClosedError:
                pass

    setattr(TempClass, method, run_with_fixers)
    TempClass.__name__ = connection_cls.__name__ + "With_" + method + "_Fixes"
    return TempClass


def add_init_decorator(function, run_before=False):
    def adder(connection):
        original_init = connection.__init__

        def new_init(self, device_id=None, filter_wireless_devices=False):
            def run():
                try:
                    function(self, device_id)
                except Exception as e:
                    self.log.warn("Init decorator {} failed".format(function.__name__), exc_info=e)
                    raise

            if run_before:
                run()
            original_init(self, device_id, filter_wireless_devices)
            if not run_before:
                run()

        connection.__init__ = new_init
        return connection

    return adder


def add_disconnect_decorator(function, run_before=False):
    def adder(connection):
        original_disconnect = connection.disconnect

        def new_disconnect(self):
            def run():
                try:
                    function(self)
                except Exception as e:
                    self.log.warn("Disconnect decorator {} failed".format(function.__name__), exc_info=e)

            if run_before:
                run()
            original_disconnect(self)
            if not run_before:
                run()

        connection.disconnect = new_disconnect
        return connection

    return adder
