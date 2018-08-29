def add_rooted_impl(connection):
    connection.adb("root")
    connection.adb("remount")
    return connection


def check_device_connected():
    """
    @rtype: bool
    """
    raise NotImplementedError


def add_some_recovery(function):
    def inner(connection):
        old_adb = connection.adb

        def new_adb(self, *args):
            if not check_device_connected():
                function(connection)

            return old_adb(self, *args)

        connection.adb = new_adb
        return connection

    return inner


def auto_fixes(connection):
    pass


def manual_fixes(connection):
    pass
