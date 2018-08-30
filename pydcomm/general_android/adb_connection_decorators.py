def add_rooted_impl(connection):
    connection.adb("root")
    connection.adb("remount")
    return connection


def add_adb_recovery_decorator(function):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, *args):
            if not self.get_connection_status()['is_connected']:
                function(self)
            return old_adb(self, *args)

        connection.adb = new_adb
        return connection

    return inner


def auto_fixes(connection):
    pass


def manual_fixes(connection):
    pass
