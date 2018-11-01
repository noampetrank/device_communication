# TODO: Add timing and logs
def add_adb_recovery_decorator(fix_function, fix_name):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, command, timeout=None, specific_device=True, disable_fixers=False):
            if not disable_fixers and specific_device and not self.test_connection():
                try:
                    fix_function(self)
                except Exception as e:
                    self.log.warn("Fix {} failed ".format(fix_name), exc_info=e)
            return old_adb(self, command, timeout, specific_device, disable_fixers)

        connection.adb = new_adb
        return connection

    return inner


# TODO: Add error handling?
def add_init_decorator(function, function_name, run_before=False):
    def adder(connection):
        original_init = connection.__init__

        def new_init(self, device_id=None):
            if run_before:
                function(self,device_id)
            original_init(self, device_id)
            if not run_before:
                function(self, device_id)

        connection.__init__ = new_init
        return connection

    return adder