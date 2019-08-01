import subprocess32 as subprocess
import grpc
import sys
import os
import time

from pydcomm.public.deviceutils.media_player_utils import DEVICE_MUSIC_PATH
from pydcomm.public.ux_benchmarks.common_extra_stats import get_device_wifi_network_name
from pydcomm.public.ux_benchmarks.common_extra_stats import CommonExtraStats
from pydcomm.public.bugarpc import IRemoteProcedureClient, IRemoteProcedureStreamingClient, IRemoteProcedureClientFactory, RpcError, ReaderWriterStream
from pydcomm.rpc.common import GReaderWriterStream
from pydcomm.rpc.gen.buga_rpc_pb2_grpc import DeviceRpcStub, DeviceRpcStreamingStub
from pydcomm.rpc.gen.buga_rpc_pb2 import GRequest, GResponse


class GRemoteProcedureClient(IRemoteProcedureClient, CommonExtraStats):
    MAX_MESSAGE_SIZE = 1024*1024*1024  # 1Gb

    def __init__(self, ip_port):
        self.host_port = ip_port

        self._create_grpc_channel_and_stub()

        self.latest_device_wifi = None
        self.latest_device_wifi_update = 0

        xver = self.get_executor_version()

    def _create_grpc_channel_and_stub(self):
        # This needs to remain an instance variable (according to https://blog.jeffli.me/blog/2017/08/02/keep-python-grpc-client-connection-truly-alive/)
        self.channel = grpc.insecure_channel(self.host_port, options=[('grpc.max_send_message_length', self.MAX_MESSAGE_SIZE),
                                                                      ('grpc.max_receive_message_length', self.MAX_MESSAGE_SIZE)])
        self.stub = DeviceRpcStub(self.channel)

    def __extra_stats__(self):
        common = super(GRemoteProcedureClient, self).__extra_stats__()
        device_id = None
        try:
            device_id = self.host_port.split(":")[0]
        except Exception:
            pass
        if time.time() - self.latest_device_wifi_update > 60:  # update every minute
            try:
                if device_id:
                    self.latest_device_wifi = get_device_wifi_network_name(device_id)
                    self.latest_device_wifi_update = time.time()
            except Exception:
                pass
        common.update({
            "device_id": device_id,
            "device_wifi": self.latest_device_wifi,
        })
        return common

    def stop(self):
        self.call('_rpc_stop', '')

    def get_version(self):
        return '1.0'

    def call(self, procedure_name, params):
        for do_retry in (True, False):
            try:
                response = self.stub.call(GRequest(name=procedure_name, buf=params))
                return response.buf
            except grpc.RpcError as ex:
                if do_retry:
                    self._create_grpc_channel_and_stub()
                else:
                    raise RpcError(grpc_exception=ex)


class GRemoteProcedureStreamingClient(IRemoteProcedureStreamingClient, GRemoteProcedureClient):
    def _create_grpc_channel_and_stub(self):
        # This needs to remain an instance variable (according to https://blog.jeffli.me/blog/2017/08/02/keep-python-grpc-client-connection-truly-alive/)
        self.channel = grpc.insecure_channel(self.host_port, options=[('grpc.max_send_message_length', self.MAX_MESSAGE_SIZE),
                                                                      ('grpc.max_receive_message_length', self.MAX_MESSAGE_SIZE)])
        self.stub = DeviceRpcStreamingStub(self.channel)

    def call_streaming(self, procedure_name, params):
        """
        Calls a streaming procedure with the params, and returns an iterator of streamed resuls.

        :param str procedure_name: Name of procedure that device side handles.
        :param str params: String to send.
        :return: Iterator of streamed results from device.
        :rtype: ReaderWriterStream
        """
        from Queue import Queue
        from threading import Event
        queue = Queue()
        end_write_sential = object()

        def read_from_queue():
            yield GResponse(buf=procedure_name)
            yield GResponse(buf=params)

            while True:
                value = queue.get()
                if value is end_write_sential:
                    raise StopIteration
                else:
                    yield GResponse(buf=value)

        res = self.stub.call_streaming(read_from_queue())

        return GReaderWriterStream(res, queue, end_write_sential)

# region Client factories common stuff


# noinspection PyAbstractClass
class _GRpcClientFactory(IRemoteProcedureClientFactory, CommonExtraStats):
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


def _push_mv(device_id, src, dst, minspeed_mbps=.05):
    # TODO Michael: use DeviceUtils.adb() when the new API is implemented (search entire file)
    file_size_mb = os.path.getsize(src) / 2.**20
    timeout = file_size_mb / minspeed_mbps + 15
    tmp_dir = "/sdcard/tmp"
    tmp_name = os.path.join(tmp_dir, os.path.basename(src))
    subprocess.check_output("adb -s {} shell mkdir -p {}".format(device_id, tmp_dir), shell=True, timeout=15)
    subprocess.check_output("adb -s {} push {} {}".format(device_id, src, tmp_name), shell=True, timeout=timeout)
    subprocess.check_output("adb -s {} shell mv {} {}".format(device_id, tmp_name, dst), shell=True, timeout=15)

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
            subprocess.check_output("adb -s {} install -r {}".format(device_id, apk_path), shell=True, timeout=30)
            print("Done")

        # Push .so
        for attempt_install in (True, False):
            try:
                parent_dir = "/data/app"
                child_dir = [x for x in subprocess.check_output("adb -s {} shell ls {}".format(device_id, parent_dir),
                                                                shell=True, timeout=15).split('\n') if 'com.buga.rpcsoloader-' in x][0]
                device_so_path = "{}/{}/lib/arm64/{}.so".format(parent_dir, child_dir, rpc_id)
                break
            except IndexError:
                if attempt_install:
                    _install_apk()
                else:
                    raise RpcError("Error installing so: loader app not found on device {}".format(device_id))

        # Run app and create connection
        _print_no_newline("Running app and creating connection... ")
        subprocess.check_output("adb -s {} shell am start -a android.intent.action.MAIN com.buga.rpcsoloader/.RpcSoLoaderActivity".format(device_id), shell=True, timeout=15)
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
        subprocess.check_output("adb -s {} shell chown system:system {}".format(device_id, device_so_path), shell=True, timeout=15)
        subprocess.check_output("adb -s {} shell chmod +rx {}".format(device_id, device_so_path), shell=True, timeout=15)
        time.sleep(.2)
        print("Done")

        cls._run_executor(rpc_id=rpc_id, so_loader=so_loader)

# endregion


# region Client factory that replaces libbugatone

class GRpcLibbugatoneLinuxClientFactory(_GRpcClientFactory):
    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        pass


class GRpcLibbugatoneAndroidClientFactory(_GRpcClientFactory):
    SILENCE_FILENAME = "silence_1h.mp3"

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
        _push_mv(device_id, local_silence_path, DEVICE_MUSIC_PATH)

        # Make sure a headset is connected so Bugatone would work
        cls._ensure_headset_connected(device_id)

        # Set port of rpc_id on device
        subprocess.check_output("adb -s {} shell setprop buga.rpc.libbugatone_executor_port {}".format(device_id, rpc_id), shell=True, timeout=15)

        # Build "satellite" .so's
        device_comm_sos = ('librpc_bugatone_proxy.so', 'librpc_server.so', 'libproto.so')

        def _satellite_sos_exist(path):
            return all(os.path.isfile(os.path.join(path, f)) for f in device_comm_sos)

        cpp_path = os.path.join(os.path.dirname(__file__), "../../cpp")
        local_libs_path = os.path.join(cpp_path, "./release/")  # First try the release dir
        if not _satellite_sos_exist(local_libs_path):
            local_libs_path = os.path.join(cpp_path, "./lib/arm64/Release/")  # Then look in build artifacts
        if not _satellite_sos_exist(local_libs_path):
            _print_no_newline("Building 'satellite' .so's... ")  # If it's not there, build device comm

            assert os.path.isdir(cpp_path)
            _build("./make.py android", cpp_path, (' * Compilation took ',
                                                   'Built target proto',
                                                   'Built target rpc_server',
                                                   'Built target rpc_bugatone_proxy',
                                                   'Built target rpc_bugatone_main',
                                                   'Built target rpc_bugatone_main_exec',
                                                   ))
            assert _satellite_sos_exist(local_libs_path)  # Couldn't build .so's, can't continue

        # Push .so's
        local_libs_path = os.path.normpath(local_libs_path)
        assert os.path.isdir(local_libs_path)
        device_lib_path = '/system/lib64'

        local_libbugatone_main_path = os.path.join(local_libs_path, "librpc_bugatone_main.so")
        device_libbugatone_main_path = os.path.join(device_lib_path, "libbugatone.so")
        libbugatone_real_path = os.path.join(device_lib_path, "libbugatone_real.so")

        subprocess.check_output("adb -s {} remount".format(device_id), shell=True, timeout=15)
        for so_name in device_comm_sos:
            local_so_path = os.path.join(local_libs_path, so_name)
            _push_mv(device_id, local_so_path, device_lib_path)

        # Push rpc_bugatone_main_exec for debug
        local_bin_path = os.path.join(cpp_path, "./bin/arm64/Release/")
        rpc_bugatone_main_exec_file = "rpc_bugatone_main_exec"
        rpc_bugatone_main_exec_local_path = os.path.join(local_bin_path, rpc_bugatone_main_exec_file)
        rpc_bugatone_main_exec_device_path = os.path.join(device_lib_path, rpc_bugatone_main_exec_file)
        if os.path.isdir(local_bin_path) and os.path.isfile(rpc_bugatone_main_exec_local_path):
            _push_mv(device_id, rpc_bugatone_main_exec_local_path, rpc_bugatone_main_exec_device_path)
            subprocess.check_output("adb -s {} shell chmod +x {}".format(device_id, rpc_bugatone_main_exec_device_path), shell=True, timeout=15)

        _push_mv(device_id, local_libbugatone_main_path, device_libbugatone_main_path)
        _push_mv(device_id, so_path, libbugatone_real_path)

        cls._restart_smart_earphone(device_id)

        cls._play_silence(device_id)
        cls._stop_playback(device_id)

    @classmethod
    def _restart_smart_earphone(cls, device_id, wasnt_running_msg="Wasn't running"):
        time.sleep(.2)
        subprocess.check_output('adb -s {} shell input keyevent 86'.format(device_id), shell=True, timeout=15)
        pid = subprocess.check_output('adb -s {} shell ps | grep com.oppo.smartearphone | $XKIT awk "{{printf \$2}}"'.format(device_id), shell=True, timeout=15).strip()
        if pid:
            subprocess.check_output("adb -s {} shell kill {}".format(device_id, pid), shell=True, timeout=15)

            for _ in range(15):
                try:
                    subprocess.check_output("adb -s {} shell kill -0 {}".format(device_id, pid), shell=True, timeout=15)
                    return
                except CalledProcessError:
                    time.sleep(0.1)
            raise RuntimeError("Couldn't kill smart earphone process")
        else:
            print(wasnt_running_msg)

    @classmethod
    def _play_silence(cls, device_id):
        # TODO this is a workaround to directly open 321Player even if it's not the default
        is_installed = "package:com.chahal.mpc.hd" in subprocess.check_output(
            'adb -s {} shell pm list packages'.format(device_id), shell=True, timeout=15)
        media_player_activity = "com.chahal.mpc.hd/org.videolan.vlc.StartActivity" if is_installed else None
        if not is_installed:
            print("321Player isn't installed on your device, it's better for everyone that you install it right now!")
            print("But I'll assume that you know what you're doing and let you continue...")

        silence_device_path = os.path.join(DEVICE_MUSIC_PATH, cls.SILENCE_FILENAME)
        subprocess.check_output(
            'adb -s {} shell am start -a android.intent.action.VIEW -d file://{} -t audio/wav --user 0{}'.format(
                device_id, silence_device_path,
                (' -n ' + media_player_activity) if media_player_activity else ''
            ), shell=True, timeout=15)  # Play
        subprocess.check_output('adb -s {} shell input keyevent 89'.format(device_id), shell=True, timeout=15)  # Rewind
        time.sleep(.2)

    @classmethod
    def _stop_playback(cls, device_id):
        subprocess.check_output('adb -s {} shell input keyevent 89'.format(device_id), shell=True, timeout=15)  # Rewind
        time.sleep(.2)
        subprocess.check_output('adb -s {} shell input keyevent 86'.format(device_id), shell=True, timeout=15)  # Stop
        time.sleep(.2)

    @classmethod
    def _ensure_headset_connected(cls, device_id):
        while True:
            audio_devices = subprocess.check_output(
                "adb -s {} shell dumpsys audio | grep -e '-\\sSTREAM_MUSIC:' -A5 | grep Devices: | cut -c 13-".format(
                    device_id), shell=True, timeout=15).split(' ')
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
                    print("Create connection failed!")
                    raise ex
                cls._play_silence(device_id)
                cls._stop_playback(device_id)
        # noinspection PyUnboundLocalVariable
        return client


# endregion


def main():
    device_id = "10.0.0.124"
    # client = GRpcSoLoaderAndroidClientFactory.create_connection(29998, device_id=device_id)
    GRpcSoLoaderAndroidClientFactory.install_executor("/home/buga/device_communication/cpp/lib/arm64/Release/libgrpc_test.so", 29999, device_id=device_id)


if __name__ == "__main__":
    main()
