import grpc
import re
from pydcomm.public.bugarpc import IRemoteProcedureClient, IRemoteProcedureClientFactory
from pydcomm.rpc.gen.buga_rpc_pb2_grpc import DeviceRpcStub
from pydcomm.rpc.gen.buga_rpc_pb2 import GRequest


class GRemoteProcedureClient(IRemoteProcedureClient):
    MAX_MESSAGE_SIZE = 1024*1024*1024  # 1Gb

    def __init__(self, ip_port):
        if ip_port is None:
            print('Using debug ')
        self.host_port = ip_port or 'localhost:33333'  # TODO remove this default

        # This needs to remain an instance variable (according to https://blog.jeffli.me/blog/2017/08/02/keep-python-grpc-client-connection-truly-alive/)
        self.channel = grpc.insecure_channel(self.host_port, options=[('grpc.max_send_message_length', self.MAX_MESSAGE_SIZE),
                                                                      ('grpc.max_receive_message_length', self.MAX_MESSAGE_SIZE)])
        self.stub = DeviceRpcStub(self.channel)
        xver = self.get_executor_version()
        assert xver == '1.0'

    def stop(self):
        self.call('_rpc_stop', '')

    def get_version(self):
        return '1.0'

    def call(self, procedure_name, params):
        response = self.stub.call(GRequest(name=procedure_name, buf=params))
        return response.buf


class GRemoteProcedureClientFactory(IRemoteProcedureClientFactory):
    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        if device_id is None:
            device_id = cls.choose_device_id()
        ip_port = "{}:{}".format(device_id, rpc_id)
        return GRemoteProcedureClient(ip_port)


    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        if device_id is None:
            device_id = cls.choose_device_id()
        raise NotImplementedError

    @classmethod
    def choose_device_id(cls):
        return 'localhost'
        # return raw_input("Enter device IP: ")
