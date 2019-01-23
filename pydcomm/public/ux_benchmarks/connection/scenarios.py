from pydcomm.public.ux_benchmarks.connection.actions import ConnectionAction


def get_push_pull_scenario(rep_num=3, create_connections_num=10, input_lengths=(1, 1000, 1e5, 1e6, 1e7)):
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    for _ in range(rep_num):
        for _ in range(create_connections_num):
            scenario += [ConnectionAction.CREATE_CONNECTION()]
            scenario += [ConnectionAction.PUSH_PULL_RANDOM(int(l)) for l in input_lengths]
    scenario += [ConnectionAction.DISCONNECT()]
    return scenario


def get_repeating_scenario(rep_num, num_connection_check, check_interval, action, params):
    scenario = []
    for i in range(rep_num):
        scenario += [ConnectionAction.CREATE_CONNECTION()]
        for j in range(num_connection_check):
            scenario += [action(*params)]
            # TODO Add sleep here?
            # I don't remember why, there was a reason that I didn't add a sleep action. Maybe because I didn't want
            # it to appear in the table?
        scenario += [ConnectionAction.DISCONNECT()]


def get_echo_scenario(rep_num=3, num_connection_check=10, check_interval=0, echo_length=10):
    scenario = []
    for _ in range(rep_num):
        scenario += [ConnectionAction.CREATE_CONNECTION()]
        for _ in range(num_connection_check):
            scenario += [ConnectionAction.SHELL_ECHO(echo_length, check_interval)]
    return scenario


def get_old_benchmark_scenario():
    # This is how the old benchmark ran
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += get_echo_scenario(20, 5, 0)
    scenario += get_echo_scenario(7, 2, 20)
    scenario += get_echo_scenario(20, 1, 1)
    scenario += get_echo_scenario(20, 5, 0)
    scenario += get_echo_scenario(7, 2, 20)
    scenario += get_echo_scenario(20, 1, 1)
    return scenario


def get_short_benchmark_scenario():
    # This is how the old benchmark ran
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += get_echo_scenario(10, 1, 0)
    scenario += get_echo_scenario(5, 3, 0)
    return scenario


def get_big_messages_scenario(rep_num=1):
    return get_push_pull_scenario(rep_num, create_connections_num=1, input_lengths=[1e5] * 3)