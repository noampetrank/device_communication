import __builtin__
import timeit


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
            self.raw_input(*args, **kwargs)
            return
        raw_input_time = timeit.timeit(lambda: self.raw_input(*args, **kwargs), number=1)
        self.input_times.append(raw_input_time)
