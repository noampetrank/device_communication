import unittest
import mock

from pydcomm.connection import Connection
from pydcomm.remote_procedure_call import AdbIntentsProcedureCaller


class UnitTestRpc(unittest.TestCase):

    def setUp(self):
        """
        Executed in the beginning of each test
        """
        self.rpc = AdbIntentsProcedureCaller()

    def tearDown(self):
        """
        Executed in the end of each test
        """
        pass

    # region RPC unit tests

    @mock.patch.object(AdbIntentsProcedureCaller, '_send_and_wait_for_return')
    def test_version_requested(self, rpc_send):
        # TODO: call rpc.start() and verify that _send_and_wait_for_return is called with procedure_name=='_rpc_get_version'
        pass

    def test_call_fails_without_start(self, rpc_send):
        # TODO: call rpc.call() without calling rpc.start() and expect RpcNotStartedError
        pass

    def test_marshalling_with_correct_type(self, rpc_send):
        # TODO: Create dummy marshallers for int and float, call rpc.call() with parameters of types int and float, make sure the correct marshaller is called with the correct parameter.
        pass

    # endregion
