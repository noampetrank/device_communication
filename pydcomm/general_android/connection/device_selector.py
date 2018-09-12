from enum import IntEnum


class MultiDeviceBehavior(IntEnum):
    CHOOSE_FIRST = 1
    USER_CHOICE = 2


def add_choose_first_behavior(connection):
    """
    :type connection: AdbConnection
    :rtype: AdbConnection
    """
    return connection


def add_user_choice_behavior(connection):
    """
    :type connection: AdbConnection
    :rtype: AdbConnection
    """
    return connection
