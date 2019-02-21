from __future__ import print_function

from pybuga.infra.utils.user_input import UserInput

from pydcomm.general_android.connection.fixers.adb_connect_fixer import adb_connect_fix


def call_a_developer_fix(connection):
    print("Please call a developer!!!")

    connection_fixed = False
    while not connection_fixed:
        if not UserInput.yes_no("Do you want to try again? [y/n]"):
            break
        adb_connect_fix(connection)
        connection_fixed = connection.test_connection()
