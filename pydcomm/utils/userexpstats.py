import time
from collections import namedtuple
from functools import wraps
from types import FunctionType

namedtuple("ApiCall", "class_name, function_name, start_time, end_time, manual_times,exception_msg, is_exception".split(", "))

api_stats = []
"""@type: ApiCall"""


def save_raw_input_time(funcname, start, end):
    """
    Called after each `raw_input` call with top most function marked with `collectstats` and time of start and finish
    input. Saves the data, currently simply in the module.

    TODO: Save data to disk.

    :param str funcname: Name of top most function marked with `collectstats` at time of calling `raw_input`.
    :param float start: Time at which `raw_input` was called.
    :param float end: Time at which `raw_input` returned.
    """
    raw_input_stats.append((funcname, start, end))


def save_exception(funcname, e, tme):
    """
    Called after exception is thrown, with top most function marked `collectstats`, the exception, and time of
    exception. Saves the data, currently simple in the module.

    TODO: Save data to disk.

    :param str funcname: Name of top most function marked with `collectstats` at time of exception.
    :param Exception e: The exception.
    :param float tme: Time of exception.
    """
    exception_stats.append((funcname, e, tme))


_fake_sentinel = object()


def collectstats(func):
    """
    Decorator for functions to collect stats on `raw_input` and exceptions.

    :param func: Function to decorate.
    :return: Decorated function.
    """
    fake_raw_input = make_fake_raw_input(func.__name__)
    fake_raw_input._UserExperienceStats_fake = _fake_sentinel

    @wraps(func)
    def newfunc(*args, **kwargs):
        import __builtin__
        orig = __builtin__.raw_input

        if getattr(orig, "_UserExperienceStats_fake", None) is not _fake_sentinel:
            try:
                __builtin__.raw_input = fake_raw_input
                return func(*args, **kwargs)
            except Exception as e:
                save_exception(func.__name__, e, time.time())
                raise
            finally:
                __builtin__.raw_input = orig
        else:
            return func(*args, **kwargs)

    return newfunc


def decorateallfuncs(wrapper):
    class DecorateAllCalls(type):
        _wrapper = wrapper

        def __new__(mcs, name, bases, class_dict):
            new_class_dict = {}
            for attrname, attr in class_dict.items():
                if isinstance(attr, FunctionType):
                    attr = wrapper(attr)
                new_class_dict[attrname] = attr

            return type.__new__(mcs, name, bases, new_class_dict)

    return DecorateAllCalls


def make_fake_raw_input(funcname):
    import __builtin__
    orig = __builtin__.raw_input

    def fake_raw_input(*args2, **kwargs2):
        st = time.time()
        try:
            return orig(*args2, **kwargs2)
        finally:
            save_raw_input_time(funcname, st, time.time())

    return fake_raw_input
