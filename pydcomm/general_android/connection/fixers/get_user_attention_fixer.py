import os


def get_user_attention_fix(connection):
    """
    This fixer Notifies the user that manual fixes are about to run.
    It's needed for getting user attention and avoid wasting time waiting for user input, and for ignoring the time
    before user attention was taken when measuring the time needed for each manual fixer to run.
    :type connection: InternalAdbConnection
    :param connection: The connection to fix (ignored)
    """
    print("Manual fixes required! Please press enter when you're ready to do them.")
    os.system('spd-say "Manual fixes required" -t child_female -r -50 -p 100')
    raw_input()
