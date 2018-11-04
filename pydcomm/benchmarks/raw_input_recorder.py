import timeit


class RawInputRecorder(object):
    def __init__(self, ignore_first=False):
        self.input_times = []
        self.ignore_first = ignore_first
        self.is_first_time = True

    def get_total_input_time(self):
        return sum(self.input_times)

    def reset_counter(self):
        self.input_times = []

    def __call__(self, *args, **kwargs):
        if self.ignore_first and self.is_first_time:
            self.is_first_time = False
            raw_input(*args, **kwargs)
            return
        raw_input_time = timeit.timeit(lambda: raw_input(*args, **kwargs), number=1)
        self.input_times.append(raw_input_time)
