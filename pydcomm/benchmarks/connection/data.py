class ApiCallData(object):
    def __init__(self, type, total_time, success, manual_interactions_count, manual_times, failure_reason):
        self.type = type
        self.total_time = total_time
        self.success = success
        self.manual_interactions_count = manual_interactions_count
        self.manual_times = manual_times
        self.failure_reason = failure_reason

    def __repr__(self):
        return "{}, {}".format(type(self).__name__, self.__dict__)


class TestDefinition(object):
    def __init__(self, rounds, num_connection_checks, check_interval):
        self.rounds = rounds
        self.num_connection_checks = num_connection_checks
        self.check_interval = check_interval

    def __repr__(self):
        # Temporary
        return "{}x{}x{}".format(self.rounds, self.num_connection_checks, self.check_interval)
        # return "{} <num_connection_checks={}, check_interval={}>".format(self.__class__.__name__, self.num_connection_checks, self.check_interval)


class PerCallTestResult(object):
    def __init__(self, total_calls, mean_time, mean_manual_fix_time, success_amount, manual_fix_pct, adb_connection_error_pct, timeout_error_pct):
        """
        :type total_calls: int
        :type mean_time: float
        :type mean_manual_fix_time: float
        :type success_amount: int
        :type manual_fix_pct: float
        :type adb_connection_error_pct: float
        :type timeout_error_pct: float
        """
        self.total_calls = total_calls
        self.mean_time = mean_time
        self.mean_manual_fix_time = mean_manual_fix_time
        self.success_amount = success_amount
        self.manual_fix_pct = manual_fix_pct
        self.adb_connection_error_pct = adb_connection_error_pct
        self.timeout_error_pct = timeout_error_pct

    def __repr__(self):
        return "{}, {}".format(type(self).__name__, self.__dict__)


class TestResult(object):
    def __init__(self, rounds, test_definition, success_count, timeout_exceptions, adb_connection_errors, total_manual_fix_count, median_fix_time, connection_failed, connect_data,
                 adb_data, disconnect_data):
        self.rounds = rounds
        self.test_definition = test_definition
        self.success_count = success_count
        self.timeout_exceptions = timeout_exceptions
        self.adb_connection_errors = adb_connection_errors
        self.total_manual_fix_count = total_manual_fix_count
        self.median_fix_time = median_fix_time
        self.connection_failed = connection_failed
        self.connect_data = connect_data  # type: PerCallTestResult
        self.adb_data = adb_data  # type: PerCallTestResult
        self.disconnect_data = disconnect_data  # type: PerCallTestResult

    def __repr__(self):
        return "{}, {}".format(type(self).__name__, self.__dict__)
