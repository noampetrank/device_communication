# TODO: Add timing and logs
def add_adb_recovery_decorator(fix_function):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, *params):
            if not self.test_connection():
                try:
                    fix_function(self)
                except Exception as e:
                    self.log.warn("Fix {} failed ".format(fix_function.__name__), exc_info=e)
            return old_adb(self, *params)

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

            if run_before:
                run()
            original_init(self, device_id)
            if not run_before:
                run()

        connection.__init__ = new_init
        return connection

    return adder
