import subprocess
import grpc
import sys
import os
import time
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
class _GRpcClientFactory(IRemoteProcedureClientFactory):
    SO_LOADER_RPC_ID = 29998

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        return cls._create_connection(device_id, rpc_id)[0]

    @classmethod
    def _create_connection(cls, device_id, rpc_id):
        if device_id is None:
            device_id = cls.choose_device_id()
        ip_port = "{}:{}".format(device_id, rpc_id)
        return GRemoteProcedureClient(ip_port), device_id

    @classmethod
    def choose_device_id(cls):
        return raw_input("Enter device IP: ")


# region Client factory that uses SO loader

# noinspection PyAbstractClass
class _GRpcSoLoaderClientFactory(_GRpcClientFactory):
    @classmethod
    def _run_executor(cls, rpc_id, so_loader, ret_inst="OK"):
        ret_run = (ret_inst == 'OK') and so_loader.call('run_so', str(rpc_id))
        if not (ret_inst == ret_run == 'OK'):
            raise RpcError("Error installing so (ret_inst={}, ret_run={})". format(ret_inst, ret_run))


class GRemoteProcedureClientLinuxFactory(_GRpcSoLoaderClientFactory):
    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        so_loader, device_id = cls._create_connection(device_id, cls.SO_LOADER_RPC_ID)
        so_loader.call("stop_so", str(rpc_id))
        with open(so_path, 'rb') as so_file:
            so_content = so_file.read()
        ret_inst = so_loader.call('install_so', '{},{}'.format(rpc_id, so_content))
        cls._run_executor(rpc_id=rpc_id, so_loader=so_loader, ret_inst=ret_inst)

    @classmethod
    def choose_device_id(cls):
        print("Choosing device_id='localhost'")
        return 'localhost'


class GRemoteProcedureClientAndroidFactory(_GRpcSoLoaderClientFactory):
    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        if device_id is None:
            device_id = cls.choose_device_id()

        def _install_apk():
            # Build APK
            app_base_path = os.path.join(os.path.dirname(__file__), "../../android/BugaRpcSoLoader")
            assert os.path.isdir(app_base_path)
            import sys
            if [x for x in sys.modules.keys() if 'idlespork' in x]:
                print("(the following can get stuck, if that happens go to the terminal from which you ran idlespork and run the command fg)")
            sys.stdout.write("Building APK... ")
            sys.stdout.flush()
            try:
                build_output = subprocess.check_output("./gradlew assembleDebug", cwd=app_base_path, shell=True)
                if '\nBUILD SUCCESSFUL in ' not in build_output:
                    print("Build failed, try to build in the terminal to see why.")
                    raise RpcError("Build failed", details=build_output)
                print("Done")
            except subprocess.CalledProcessError as ex:
                print("Build failed, try to build in the terminal to see why.")
                raise RpcError("Build failed", original_exception=ex)

            # Install APK
            sys.stdout.write("Installing APK... ")
            sys.stdout.flush()
            apk_path = os.path.join(app_base_path, "./app/build/outputs/apk/debug/app-debug.apk")
            assert os.path.isfile(apk_path)
            # TODO Michael: use DeviceUtils.adb() when the new API is implemented
            subprocess.check_output("adb -s {} install -r {}".format(device_id, apk_path), shell=True)
            print("Done")

        # Push .so
        for attempt_install in (True, False):
            try:
                parent_dir = "/data/app"
                child_dir = [x for x in subprocess.check_output("adb -s {} shell ls {}".format(device_id, parent_dir), shell=True).split('\n') if 'com.buga.rpcsoloader-' in x][0]
                device_so_path = "{}/{}/lib/arm64/{}.so".format(parent_dir, child_dir, rpc_id)
            except IndexError:
                if attempt_install:
                    _install_apk()
                else:
                    raise RpcError("Error installing so: loader app not found on device {}".format(device_id))

        # Run app and create connection
        sys.stdout.write("Running app and creating connection... ")
        sys.stdout.flush()
        subprocess.check_output("adb -s {} shell am start -a android.intent.action.MAIN com.buga.rpcsoloader/.RpcSoLoaderActivity".format(device_id), shell=True)
        for attempts_left in reversed(range(5)):
            try:
                so_loader, device_id = cls._create_connection(device_id, cls.SO_LOADER_RPC_ID)
            except RpcError as ex:
                if attempts_left:
                    time.sleep(0.5)
                else:
                    raise ex
        print("Done")

        # noinspection PyUnboundLocalVariable
        so_loader.call("stop_so", str(rpc_id))

        sys.stdout.write("Pushing {}... ".format(os.path.basename(so_path)))
        sys.stdout.flush()
        # noinspection PyUnboundLocalVariable
        subprocess.check_output("adb -s {} push {} {}".format(device_id, so_path, device_so_path), shell=True)
        print("Done")
        cls._run_executor(rpc_id=rpc_id, so_loader=so_loader)

    @classmethod
    def choose_device_id(cls):
        print("Choosing device_id='10.0.0.138'")
        return '10.0.0.138'
# endregion


# region Client factory that replaces libbugatone

class GRpcLibbugatoneClientFactory(_GRpcClientFactory):
    LIBBUGATONE_RPC_ID = 31000

    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        client, device_id = cls._create_connection(device_id, cls.SO_LOADER_RPC_ID)
        # TODO Michael: use DeviceUtils.adb() when the new API is implemented
        device_lib_path = '/system/lib64'
        orig_libbugatone_path = os.path.join(device_lib_path, "libbugatone.so")
        moved_libbugatone_path = os.path.join(device_lib_path, "libbugatone_real.so")
        subprocess.check_output("adb -s {} shell mv {} {}".format(device_id, orig_libbugatone_path, moved_libbugatone_path), shell=True)
        subprocess.check_output("adb -s {} push {} {}".format(device_id, so_path, orig_libbugatone_path), shell=True)

        # TODO +compile
        import os
        sos_dir = os.path.dirname(so_path)
        subprocess.check_output("adb -s {} push {} {}".format(device_id, os.path.join(sos_dir, ), orig_libbugatone_path), shell=True)

        # TODO push silence
        # TODO create_connection should restart smart earphone; play silence (ask Ziv), maybe fake connect earphone (or check if earphone connected)
        # TODO create_conn pushes port to prop, checks headphones, then plays silence


#endregion
