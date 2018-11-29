import grpc
import re
from pydcomm.public.bugarpc import IRemoteProcedureClient, IRemoteProcedureClientFactory, RpcError
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
        try:
            response = self.stub.call(GRequest(name=procedure_name, buf=params))
        except grpc.RpcError as ex:
            raise RpcError(grpc_exception=ex)
        return response.buf


class GRemoteProcedureClientFactory(IRemoteProcedureClientFactory):
    SO_LOADER_RPC_ID = 29998

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        return cls._create_connection(device_id, rpc_id)[0]

    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        with open(so_path, 'rb') as so_file:
            so_content = so_file.read()
        so_loader, device_id = cls._create_connection(device_id)
        ret_inst = so_loader.call('install_so', '{},{}'.format(rpc_id, so_content))
        ret_run = (ret_inst == 'OK') and so_loader.call('run_so', str(rpc_id))
        if not (ret_inst == ret_run == 'OK'):
            raise RpcError("Error installing so (ret_inst={}, ret_run={})". format(ret_inst, ret_run))

    @classmethod
    def choose_device_id(cls):
        return 'localhost'
        # return raw_input("Enter device IP: ")

    @classmethod
    def _create_connection(cls, device_id, rpc_id=None):
        if device_id is None:
            device_id = cls.choose_device_id()
        rpc_id = rpc_id or cls.SO_LOADER_RPC_ID
        so_loader_ip_port = "{}:{}".format(device_id, rpc_id)
        return GRemoteProcedureClient(so_loader_ip_port), device_id
