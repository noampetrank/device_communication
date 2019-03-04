from traceback import print_exc

from pybuga.infra.utils.user_input import UserInput

from pydcomm.public.iconnection import ConnectionClosedError


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
        fixers.append(lambda *args, **kwargs: None)     # Add 'do nothing' fixer to allow recovery after the last fix
        for fix in fixers:
            try:
                return old_method(*args, **kwargs)
            except ConnectionClosedError:
                if kwargs.get("disable_fixers", False):
                    raise
                try:
                    fix(args[0])
                except Exception:
                    print_exc()
                    raise
        print("please call a developer.")
        while True:
            if not UserInput.yes_no("Do you want to try again? [y/n]"):
                raise ConnectionClosedError()
            try:
                return old_method(*args, **kwargs)
            except ConnectionClosedError:
                pass

    setattr(TempClass, method, run_with_fixers)
    TempClass.__name__ = connection_cls.__name__ + "With_" + method + "_Fixes"
    return TempClass


def add_init_decorator(function, run_before=False):
    def adder(connection):
        original_init = connection.__init__

        class TempClass(connection):
            pass

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

        TempClass.__init__ = new_init
        TempClass.__name__ = connection.__name__
        return TempClass

    return adder


def add_disconnect_decorator(function, run_before=False):
    def adder(connection):
        original_disconnect = connection.disconnect

        class TempClass(connection):
            pass

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

        TempClass.disconnect = new_disconnect
        TempClass.__name__ = connection.__name__
        return TempClass

    return adder
