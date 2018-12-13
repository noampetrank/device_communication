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

    @classmethod
    def _build(cls, cmd, cwd, expected_output_strings, ok_message="Done", exception_message="Build failed", error_message="Build failed, try to build in the terminal to see why."):
        try:
            build_output = subprocess.check_output(cmd, cwd=cwd, shell=True)
            missing_output_string = [x for x in expected_output_strings if x not in build_output]
            if missing_output_string:
                print(error_message)
                print("Missing output strings: {}".format(', '.join(missing_output_string)))
                raise RpcError(exception_message, details=build_output)
            print(ok_message)
        except subprocess.CalledProcessError as ex:
            print(error_message)
            raise RpcError(exception_message, original_exception=ex)


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
            cls._build("./gradlew assembleDebug", app_base_path, ('\nBUILD SUCCESSFUL in ',))

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

# endregion


# region Client factory that replaces libbugatone

class GRpcLibbugatoneAndroidClientFactory(_GRpcClientFactory):
    # LIBBUGATONE_RPC_ID = 31000

    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        # Build "sattelite" .so's
        cpp_path = os.path.join(os.path.dirname(__file__), "../../cpp")
        assert os.path.isdir(cpp_path)
        sys.stdout.write("Building 'sattelite' .so's for benchmark... ")
        sys.stdout.flush()
        cls._build("./make.py android", cpp_path, (' * Compilation took ',
                                                   'Built target proto',
                                                   'Built target rpc_server',
                                                   'Built target rpc_bugatone_proxy',
                                                   'Built target rpc_bugatone_main',
                                                   ))

        # Push .so's
        local_libs_path = os.path.join(cpp_path, "./lib/arm64/Release/")
        assert os.path.isdir(local_libs_path)
        device_lib_path = '/system/lib64'

        local_libbugatone_main_path = os.path.join(local_libs_path, "librpc_bugatone_main.so")
        device_libbugatone_main_path = os.path.join(device_lib_path, "libbugatone.so")
        libbugatone_real_path = os.path.join(device_lib_path, "libbugatone_real.so")

        # client, device_id = cls._create_connection(device_id, cls.SO_LOADER_RPC_ID)
        # TODO Michael: use DeviceUtils.adb() when the new API is implemented
        for so_name in ('librpc_bugatone_proxy.so', 'librpc_server.so', 'libproto.so'):
            local_so_path = os.path.join(local_libs_path, so_name)
            subprocess.check_output("adb -s {} push {} {}".format(device_id, local_so_path, device_lib_path), shell=True)

        subprocess.check_output("adb -s {} push {} {}".format(device_id, local_libbugatone_main_path, device_libbugatone_main_path), shell=True)
        subprocess.check_output("adb -s {} push {} {}".format(device_id, so_path, libbugatone_real_path), shell=True)

        # TODO push silence
        # TODO create_connection should restart smart earphone; play silence (ask Ziv), maybe fake connect earphone (or check if earphone connected)
        # TODO create_conn pushes port to prop, checks headphones, then plays silence

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        # restart_smart_earphone
        subprocess.check_output('adb shell input keyevent 86', shell=True)
        subprocess.check_output('adb shell am force-stop com.oppo.music', shell=True)
        get_pid_command = ['adb',
                           'shell',
                           'ps | grep com.oppo.smartearphone | $XKIT awk "{printf \\$2}"']
        kill_command = ['adb',
                        'shell',
                        'ps | grep com.oppo.smartearphone | $XKIT awk "{printf \$2}" | xargs kill']
        # prev_pid = subprocess.check_output(get_pid_command)
        subprocess.check_call(kill_command)
        # new_pid = subprocess.check_output(get_pid_command)
        print("restarted smart earphone")
        time.sleep(.2)

        # Play song
        subprocess.check_output("adb shell am start -a android.intent.action.VIEW -n com.oppo.music/.dialog.activity.AuditionActivity -d file:///sdcard/Music/Havana.wav", shell=True)
        time.sleep(.5)

        client, device_id = cls._create_connection(device_id, rpc_id)
        return client

    @classmethod
    def choose_device_id(cls):
        print("Choosing device_id='10.0.0.138'")
        return '10.0.0.138'


#endregion
