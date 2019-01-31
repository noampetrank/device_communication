def add_adb_recovery_decorator(fix_function):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
            old_test_connection = self.test_connection
            try:
                if not disable_fixers and specific_device:
                    if not self.test_connection():
                        try:
                            fix_function(self)
                        except Exception as e:
                            self.log.warn("Fix {} failed ".format(fix_function.__name__), exc_info=e)
                    else:
                        self.test_connection = lambda: True
                return old_adb(self, command, timeout, specific_device, disable_fixers)
            finally:
                self.test_connection = old_test_connection

        connection.adb = new_adb
        return connection

    return inner


def add_init_decorator(function, run_before=False):
    def adder(connection):
        original_init = connection.__init__

        def new_init(self, device_id=None):
            def run():
                try:
                    function(self, device_id)
                except Exception as e:
                    self.log.warn("Init decorator {} failed".format(function.__name__), exc_info=e)
                    raise

            if run_before:
                run()
            original_init(self, device_id)
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
