import subprocess
from abc import ABCMeta

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


# noinspection PyAbstractClass
class _GRemoteProcedureClientFactory(IRemoteProcedureClientFactory):
    SO_LOADER_RPC_ID = 29998

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        return cls._create_connection(device_id, rpc_id)[0]

    @classmethod
    def _run_executor(cls, rpc_id, device_id=None, ret_inst="OK"):
        so_loader, device_id = cls._create_connection(device_id)
        ret_run = (ret_inst == 'OK') and so_loader.call('run_so', str(rpc_id))
        if not (ret_inst == ret_run == 'OK'):
            raise RpcError("Error installing so (ret_inst={}, ret_run={})". format(ret_inst, ret_run))

    @classmethod
    def _create_connection(cls, device_id, rpc_id=None):
        if device_id is None:
            device_id = cls.choose_device_id()
        rpc_id = rpc_id or cls.SO_LOADER_RPC_ID
        so_loader_ip_port = "{}:{}".format(device_id, rpc_id)
        return GRemoteProcedureClient(so_loader_ip_port), device_id


class GRemoteProcedureClientLinuxFactory(_GRemoteProcedureClientFactory):
    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        so_loader, device_id = cls._create_connection(device_id)
        with open(so_path, 'rb') as so_file:
            so_content = so_file.read()
        ret_inst = so_loader.call('install_so', '{},{}'.format(rpc_id, so_content))
        _GRemoteProcedureClientFactory._run_executor(rpc_id=rpc_id, device_id=device_id, ret_inst=ret_inst)

    @classmethod
    def choose_device_id(cls):
        return 'localhost'
        # return raw_input("Enter device IP: ")


class GRemoteProcedureClientAndroidFactory(_GRemoteProcedureClientFactory):
    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        so_loader, device_id = cls._create_connection(device_id)
        # TODO Michael: use DeviceUtils.adb() when the new API is implemented
        try:
            parent_dir = "/data/app"
            child_dir = [x for x in subprocess.check_output("adb shell ls {}".format(parent_dir), shell=True).split('\n') if 'com.buga.rpcsoloader-' in x][0]
            device_so_path = "{}/{}/lib/arm64/{}.so".format(parent_dir, child_dir, rpc_id)
        except IndexError:
            raise RpcError("Error installing so: loader app not found on device {}".format(device_id))

        subprocess.check_output("adb push {} {}".format(so_path, device_so_path), shell=True)
        _GRemoteProcedureClientFactory._run_executor(rpc_id=rpc_id, device_id=device_id)

    @classmethod
    def choose_device_id(cls):
        return '10.0.0.123'
        # return raw_input("Enter device IP: ")
