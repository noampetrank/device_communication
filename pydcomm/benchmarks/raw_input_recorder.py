import __builtin__
import timeit


# https://stackoverflow.com/a/24812460/365408
# set timeit to return the value
def _template_func(setup, func):
    """Create a timer function. Used if the "statement" is a callable."""

    def inner(_it, _timer, _func=func):
        setup()
        _t0 = _timer()
        for _i in _it:
            retval = _func()
        _t1 = _timer()
        return _t1 - _t0, retval

    return inner


timeit._template_func = _template_func
class RawInputRecorder(object):
    """
    Replaces the regular raw_input with one that counts the time the user took to answer.
    >>> with RawInputRecorder() as r:
    ...    raw_input()
    ...    raw_input()
    ...    raw_input()
    >>> print(r.get_total_input_time())
    """
    def __init__(self, ignore_first=False):
        self.input_times = []
        self.ignore_first = ignore_first
        self.is_first_time = True
        self.raw_input = raw_input

    def __enter__(self):
        self.reset_counter()
        __builtin__.raw_input = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        __builtin__.raw_input = self.raw_input

    def get_total_input_time(self):
        return sum(self.input_times)

    def reset_counter(self):
        self.input_times = []

    def __call__(self, *args, **kwargs):
        if self.ignore_first and self.is_first_time:
            self.is_first_time = False
            return self.raw_input(*args, **kwargs)
        raw_input_time, retval = timeit.timeit(lambda: self.raw_input(*args, **kwargs), number=1)
        self.input_times.append(raw_input_time)
        return retval
