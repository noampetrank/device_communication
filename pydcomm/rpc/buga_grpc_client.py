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
        self.host_port = ip_port

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


# region Client factories common stuff

# noinspection PyAbstractClass
class _GRpcClientFactory(IRemoteProcedureClientFactory):
    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        return cls._create_connection(device_id, rpc_id)[0]

    @classmethod
    def _create_connection(cls, device_id, rpc_id):
        device_id = cls._choose_device_id_if_none(device_id)
        ip_port = "{}:{}".format(device_id, rpc_id)
        return GRemoteProcedureClient(ip_port), device_id

    @classmethod
    def _choose_device_id_if_none(cls, device_id):
        if device_id is None:
            device_id = cls.choose_device_id()
        return device_id

    @classmethod
    def choose_device_id(cls):
        ip = raw_input("Enter device IP: ")
        print("")
        return ip


def _print_no_newline(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def _build(cmd, cwd, expected_output_strings, ok_message="Done", exception_message="Build failed", error_message="Build failed, try to build in the terminal to see why."):
    try:
        build_output = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT, shell=True)
        missing_output_string = [x for x in expected_output_strings if x not in build_output]
        if missing_output_string:
            print(error_message)
            print("Missing output strings: {}".format(', '.join(missing_output_string)))
            raise RpcError(exception_message, details=build_output)
        print(ok_message)
    except subprocess.CalledProcessError as ex:
        print(error_message)
        raise RpcError(exception_message, original_exception=ex)


def _push_mv(device_id, src, dst):
    # TODO Michael: use DeviceUtils.adb() when the new API is implemented (search entire file)
    tmp_dir = "/sdcard/tmp"
    tmp_name = os.path.join(tmp_dir, os.path.basename(src))
    subprocess.check_output("adb -s {} shell mkdir -p {}".format(device_id, tmp_dir), shell=True)
    subprocess.check_output("adb -s {} push {} {}".format(device_id, src, tmp_name), shell=True)
    subprocess.check_output("adb -s {} shell mv {} {}".format(device_id, tmp_name, dst), shell=True)

# endregion


# region Client factory that uses SO loader

# noinspection PyAbstractClass
class _GRpcSoLoaderClientFactory(_GRpcClientFactory):
    SO_LOADER_RPC_ID = 29998

    @classmethod
    def _run_executor(cls, rpc_id, so_loader, ret_inst="OK"):
        ret_run = (ret_inst == 'OK') and so_loader.call('run_so', str(rpc_id))
        if not (ret_inst == ret_run == 'OK'):
            raise RpcError("Error installing so (ret_inst={}, ret_run={})". format(ret_inst, ret_run))


class GRpcSoLoaderLinuxClientFactory(_GRpcSoLoaderClientFactory):
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


class GRpcSoLoaderAndroidClientFactory(_GRpcSoLoaderClientFactory):
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
            _print_no_newline("Building APK... ")
            _build("./gradlew assembleDebug", app_base_path, ('\nBUILD SUCCESSFUL in ',))

            # Install APK
            _print_no_newline("Installing APK... ")
            apk_path = os.path.join(app_base_path, "./app/build/outputs/apk/debug/app-debug.apk")
            assert os.path.isfile(apk_path)
            subprocess.check_output("adb -s {} install -r {}".format(device_id, apk_path), shell=True)
            print("Done")

        # Push .so
        for attempt_install in (True, False):
            try:
                parent_dir = "/data/app"
                child_dir = [x for x in subprocess.check_output("adb -s {} shell ls {}".format(device_id, parent_dir), shell=True).split('\n') if 'com.buga.rpcsoloader-' in x][0]
                device_so_path = "{}/{}/lib/arm64/{}.so".format(parent_dir, child_dir, rpc_id)
                break
            except IndexError:
                if attempt_install:
                    _install_apk()
                else:
                    raise RpcError("Error installing so: loader app not found on device {}".format(device_id))

        # Run app and create connection
        _print_no_newline("Running app and creating connection... ")
        subprocess.check_output("adb -s {} shell am start -a android.intent.action.MAIN com.buga.rpcsoloader/.RpcSoLoaderActivity".format(device_id), shell=True)
        for attempts_left in reversed(range(5)):
            try:
                so_loader, device_id = cls._create_connection(device_id, cls.SO_LOADER_RPC_ID)
                break
            except RpcError as ex:
                if attempts_left:
                    time.sleep(0.5)
                else:
                    raise ex
        print("Done")

        # noinspection PyUnboundLocalVariable
        so_loader.call("stop_so", str(rpc_id))

        _print_no_newline("Pushing {}... ".format(os.path.basename(so_path)))
        # noinspection PyUnboundLocalVariable
        _push_mv(device_id, so_path, device_so_path)
        subprocess.check_output("adb -s {} shell chown system:system {}".format(device_id, device_so_path), shell=True)
        subprocess.check_output("adb -s {} shell chmod +rx {}".format(device_id, device_so_path), shell=True)
        time.sleep(.2)
        print("Done")

        cls._run_executor(rpc_id=rpc_id, so_loader=so_loader)

# endregion


# region Client factory that replaces libbugatone

class GRpcLibbugatoneAndroidClientFactory(_GRpcClientFactory):
    SILENCE_FILENAME = "silence_1h.mp3"
    DEVICE_MUSIC_PATH = "/sdcard/Music"

    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        device_id = cls._choose_device_id_if_none(device_id)

        # Make sure the .so exists
        if not os.path.isfile(so_path):
            raise RpcError("Executor .so not found. (if you're running benchmark - do you need to pull test-files?)")

        # Push silence
        res_path = "/home/buga/test-files/device_communication/resources"
        local_silence_path = os.path.join(res_path, cls.SILENCE_FILENAME)
        if not os.path.isdir(res_path) or not os.path.isfile(local_silence_path):
            raise RpcError("{} not found. (do you need to pull test-files?)".format(local_silence_path))
        _push_mv(device_id, local_silence_path, cls.DEVICE_MUSIC_PATH)

        # Make sure a headset is connected so Bugatone would work
        cls._ensure_headset_connected(device_id)

        # Set port of rpc_id on device
        subprocess.check_output("adb -s {} shell setprop buga.rpc.libbugatone_executor_port {}".format(device_id, rpc_id), shell=True)

        # Build "satellite" .so's
        _print_no_newline("Building 'satellite' .so's... ")
        cpp_path = os.path.join(os.path.dirname(__file__), "../../cpp")
        assert os.path.isdir(cpp_path)
        _build("./make.py android", cpp_path, (' * Compilation took ',
                                               'Built target proto',
                                               'Built target rpc_server',
                                               'Built target rpc_bugatone_proxy',
                                               'Built target rpc_bugatone_main',
                                               'Built target rpc_bugatone_main_exec',
                                               ))

        # Push .so's
        _print_no_newline("Pushing 'satellite' .so's... ")
        local_libs_path = os.path.join(cpp_path, "./lib/arm64/Release/")
        assert os.path.isdir(local_libs_path)
        device_lib_path = '/system/lib64'

        local_libbugatone_main_path = os.path.join(local_libs_path, "librpc_bugatone_main.so")
        device_libbugatone_main_path = os.path.join(device_lib_path, "libbugatone.so")
        libbugatone_real_path = os.path.join(device_lib_path, "libbugatone_real.so")

        subprocess.check_output("adb -s {} remount".format(device_id), shell=True)
        for so_name in ('librpc_bugatone_proxy.so', 'librpc_server.so', 'libproto.so'):
            local_so_path = os.path.join(local_libs_path, so_name)
            _push_mv(device_id, local_so_path, device_lib_path)

        # Push rpc_bugatone_main_exec for debug
        local_bin_path = os.path.join(cpp_path, "./bin/arm64/Release/")
        assert os.path.isdir(local_bin_path)
        _push_mv(device_id, os.path.join(local_bin_path, "rpc_bugatone_main_exec"), device_lib_path)
        subprocess.check_output("adb -s {} shell chmod +x {}/rpc_bugatone_main_exec".format(device_id, device_lib_path), shell=True)

        _push_mv(device_id, local_libbugatone_main_path, device_libbugatone_main_path)
        _push_mv(device_id, so_path, libbugatone_real_path)
        print("Done")

        _print_no_newline("Restarting smart earphone... ")
        cls._restart_smart_earphone(device_id)

        _print_no_newline("Playing music (well umm, silence)... ")
        cls._play_silence(device_id)
        print("OK")

    @classmethod
    def _restart_smart_earphone(cls, device_id, done_msg="Done", wasnt_running_msg="Wasn't running"):
        time.sleep(.2)
        subprocess.check_output('adb -s {} shell input keyevent 86'.format(device_id), shell=True)
        pid = subprocess.check_output('adb -s {} shell ps | grep com.oppo.smartearphone | $XKIT awk "{{printf \$2}}"'.format(device_id), shell=True).strip()
        if pid:
            subprocess.check_output("adb -s {} shell kill {}".format(device_id, pid), shell=True)
            time.sleep(1.5)
            print("{} (killed pid {})".format(done_msg, pid))
        else:
            print(wasnt_running_msg)

    @classmethod
    def _play_silence(cls, device_id):
        time.sleep(.2)
        subprocess.check_output('adb -s {} shell am force-stop com.oppo.music'.format(device_id), shell=True)
        time.sleep(.5)
        subprocess.check_output("adb -s {} shell am start -a android.intent.action.VIEW -n com.oppo.music/.dialog.activity.AuditionActivity -d file://{}/{}".format(device_id, cls.DEVICE_MUSIC_PATH, cls.SILENCE_FILENAME), shell=True)
        time.sleep(.5)

    @classmethod
    def _ensure_headset_connected(cls, device_id):
        while True:
            audio_devices = subprocess.check_output("adb -s {} shell dumpsys audio | grep -e '-\sSTREAM_MUSIC:' -A5 | grep Devices: | cut -c 13-".format(device_id), shell=True).split(' ')
            if 'headset' in [x.strip() for x in audio_devices]:
                break
            raw_input("Please connect earphone and press enter...")
            print("")

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        # Make sure a headset is connected so Bugatone would work
        cls._ensure_headset_connected(device_id)

        for recover_with_silence in (True, False):
            try:
                client, device_id = cls._create_connection(device_id, rpc_id)
                break
            except RpcError as ex:
                if not recover_with_silence:
                    raise ex
                cls._play_silence(device_id)
        # noinspection PyUnboundLocalVariable
        return client


# endregion


def main():
    device_id = "10.0.0.124"
    # client = GRpcSoLoaderAndroidClientFactory.create_connection(29998, device_id=device_id)
    GRpcSoLoaderAndroidClientFactory.install_executor("/home/buga/device_communication/cpp/lib/arm64/Release/libgrpc_test.so", 29999, device_id=device_id)


if __name__ == "__main__":
    main()
