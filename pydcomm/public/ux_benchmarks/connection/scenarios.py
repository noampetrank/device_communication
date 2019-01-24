from pydcomm.public.ux_benchmarks.connection.actions import ConnectionAction


def get_repeating_scenario(rep_num, action, params):
    scenario = []
    for i in range(rep_num):
        scenario += [ConnectionAction.CREATE_CONNECTION()]
        scenario += [action(x) for x in params]
        scenario += [ConnectionAction.DISCONNECT()]
    return scenario


def get_echo_scenario(rep_num=3, in_connection_repeats=10, echo_length=10):
    return get_repeating_scenario(rep_num, ConnectionAction.SHELL_ECHO, [echo_length] * in_connection_repeats)


def get_push_pull_scenario(rep_num=3, input_lengths=(1, 1000, 1e5, 1e6, 1e7)):
    return get_repeating_scenario(rep_num, ConnectionAction.PUSH_PULL_RANDOM, input_lengths)


def get_short_benchmark_scenario():
    # This is how the old benchmark ran
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += get_repeating_scenario(3, ConnectionAction.SHELL_ECHO, [2000] * 10)
    return scenario


def get_complete_benchmark(repeats=1):
    scenario = []
    scenario += [ConnectionAction.CHOOSE_DEVICE_ID()]
    scenario += [ConnectionAction.CREATE_CONNECTION(), ConnectionAction.ROOT(), ConnectionAction.REMOUNT(),
                 ConnectionAction.DISCONNECT()]
    scenario += get_repeating_scenario(repeats, ConnectionAction.PUSH_PULL_RANDOM,
                                       [2880000, 5760000, 11520000, 69120000])  # 5s, 10s, 20s, 120s
    scenario += get_repeating_scenario(repeats, ConnectionAction.SHELL_ECHO,
                                       [100, 200, 300, 1000])
    return scenario
