import __builtin__
import time
import unittest

from pydcomm.benchmarks.raw_input_recorder import RawInputRecorder
from pydcomm.tests.helpers import TestCasePatcher


class TesterRawInputTests(unittest.TestCase):
    def setUp(self):
        self.patcher = TestCasePatcher(self)
        self.mock_raw_input = self.patcher.addObjectPatch(__builtin__, "raw_input")
        self.mock_raw_input.side_effect = self.my_raw_input
        self.mock_calls = []  # type: list[tuple[str,int]]
        self.mock_calls_index = 0

        self.mock_timeit = self.patcher.addPatch("pydcomm.benchmarks.raw_input_recorder.timeit.timeit")
        self.mock_timeit.side_effect = self.my_timeit

    def my_timeit(self, *args, **kwargs):
        if self.mock_calls_index >= len(self.mock_calls):
            raise Exception("Not enough mock_calls given")
        current = self.mock_calls[self.mock_calls_index]
        self.mock_calls_index += 1
        return current[1]

    def my_raw_input(self, *args):
        if self.mock_calls_index >= len(self.mock_calls):
            raise Exception("Not enough mock_calls given")
        current = self.mock_calls[self.mock_calls_index]
        self.mock_calls_index += 1
        time.sleep(current[1])
        return current[0]

    def test_raw_input__ignore_first_is_true__first_call_is_ignored(self):
        self.mock_calls.append(("", 1))
        tester_raw_input = RawInputRecorder(ignore_first=True)
        tester_raw_input()
        self.assertEqual(tester_raw_input.get_total_input_time(), 0)

    def test_raw_input__two_calls__sum_of_calls_returned(self):
        self.mock_calls.append(("", 1))
        self.mock_calls.append(("", 1))
        tester_raw_input = RawInputRecorder()
        tester_raw_input()
        tester_raw_input()
        self.assertEqual(tester_raw_input.get_total_input_time(), 2)

    def test_raw_input__reset_counter__dont_count_previous_calls(self):
        self.mock_calls.append(("", 3))
        self.mock_calls.append(("", 1))
        tester_raw_input = RawInputRecorder()
        tester_raw_input()
        tester_raw_input.reset_counter()
        tester_raw_input()
        self.assertEqual(tester_raw_input.get_total_input_time(), 1)

    def test_contextmanager__normal_usage__return_sum_of_times_per_Wih_run(self):
        self.mock_calls.append(("", 3))
        self.mock_calls.append(("", 1))
        self.mock_calls.append(("", 4))
        with RawInputRecorder() as r:
            raw_input()
            raw_input()
            raw_input()
        self.assertEqual(r.get_total_input_time(), 3+1+4)

        self.mock_calls.append(("",2))
        with r:
            raw_input()
        self.assertEqual(r.get_total_input_time(),2)
