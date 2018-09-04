import grpc
from pydcomm.rpc.remote_procedure_call import StandardRemoteProcedureCaller
from pydcomm.rpc.gen.buga_rpc_pb2_grpc import DeviceRpcStub
from pydcomm.rpc.gen.buga_rpc_pb2 import GRequest


class BugaGRpcCaller(StandardRemoteProcedureCaller):
    def __init__(self, ip_port):
        self.ip_port = ip_port or 'localhost:50051'  # TODO remove this default
        self.channel = None
        self.stub = None

    def start(self):
        # TODO connect to IP:port
        self.channel = grpc.insecure_channel(self.ip_port)
        self.stub = DeviceRpcStub(self.channel)
        xver = self.get_executor_version()
        assert xver == '0.0'

    def stop(self):
        pass

    def _echo_test(self):
        response = self.stub.grpc_echo(GRequest(buf='Python client works!'))
        print("RPC client received: " + response.buf)
        response = self.stub.call(GRequest(name='_rpc_echo', buf='Python Buga client works!'))
        print("RPC client received: " + response.buf)
        xver = self.get_executor_version()
        print("Executor version {}".format(xver))

    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        """
        Specific implementation that calls a procedure on the executor and returns values from it.
        :param procedure_name:
        :param marshalled_params:
        :return:
        """
        response = self.stub.call(GRequest(name=procedure_name, buf=marshalled_params))
        return response.buf
