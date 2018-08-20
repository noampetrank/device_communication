import os


#############################################


class ConnectionMonitor:
    """
    Connects to a device and maintains the connection.
    """

    def __init__(self, device_id_or_ip=None):
        # Connect to device
        self.device_id = device_id_or_ip
        pass

    def get_connection_status(self):
        """
        :return: dict object with the following fields:
            is_connected: bool
            is_wireless: bool
            connection_type: string in ('usb_debugging', 'mtp', 'file_transfer')
            device_id_or_ip: string
        """
        return dict(is_connected=True, is_wireless=False, connection_type='usb_debugging')

    def disconnect(self):
        """
        :return: -
        """
        pass

    def _handle_exception(self, exc_info):
        """
        Handles an exception or raises it if it couldn't be handled.
        :param exc_info: value of os.exc_info()
        """
        pass

    def adb(self, *args):
        """
        :type args: list(str)
        :param args: array of splitted args to adb command
        """
        pass

    @staticmethod
    def restart_adb_server():
        """
        adb kill-server & adb start-start
        """
        pass


class AutoRecoveringConnectionMonitor(ConnectionMonitor):
    def _handle_exception(self, exc_info):
        pass


class TroubleshootingConnectionMonitor(AutoRecoveringConnectionMonitor):
    def _handle_exception(self, exc_info):
        pass


#############################################


class RootedDecorator:
    """
    Adds remount to ConnectionMonitor objects
    """

    def __init__(self, decoratee):
        """
        :param decoratee: of the ConnectionMonitor family
        """
        self.decoratee = decoratee
        self._remount()

    def check_connection(self):
        self._remount()
        self.decoratee.check_connection()

    def __getattr__(self, item):
        return getattr(self.decoratee, item)

    def __setattr__(self, item, value):
        return setattr(self.decoratee, item, value)


#############################################


class DeviceUtils:
    def __init__(self, connection):
        self.connection = connection

    ## Probably non-device specific ##

    def push(self, local_path, path_on_device):
        """
        Push a file/dir to the device.
        :type local_path: str
        :type path_on_device: str
        """
        pass

    def pull(self, path_on_device, local_path):
        """
        Pull a file/dir to the device.
        :type path_on_device: str
        :type local_path: str
        """
        pass

    def send_intent(self, action, name, **args):
        """
        :type action:  str
        :type name: str
        :type args: dict[str, str]
        :return:
        """
        pass

    def shell(self, *args):
        """
        :type args: list(str)
        """
        pass

    def mkdir(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def touch_file(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def ls(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def get_time(self):
        """
        :rtype: datetime
        """
        pass

    def remove(self, path_on_device):
        """
        :type path_on_device: str
        """
        pass

    def get_device_name(self):
        """
        :rtype: str
        """
        pass

    def set_prop(self, prop_name, value):
        """
        :type prop_name: str
        :type value: str
        """
        pass

    def reboot(self):
        """
        """
        pass

    ## Possibly device specific ##
    def is_earphone_connected(self):
        """
        :rtype: bool
        """
        pass

    def get_volume(self):
        """
        :rtype: int
        """
        pass

    def set_volume(self, val):
        """
        :type val: int
        """
        pass

    def is_max_volume(self):
        """
        :rtype: bool
        """
        pass


#############################################


class Serializer:
    """
    interface of classes used to serialize / deserialize data to / from binary
    this way business logic of what the data is is decoupled from
    how to send and receive it
    """

    def __init__(self):
        pass

    def serialize(self, data):
        """
        turn data into bytes
        :param data:
        :return: binary data
        """
        return data

    def deserialize(self, buffer):
        """
        turn bytes into data
        :type buffer: binary data
        :return:
        """
        return buffer


#############################################


class FileBridge:
    def __init__(self, connection, serializer, device_base_folder='/sdcard/tmp/'):
        """
        :type connection: ConnectionMonitor family
        :type serializer: Serializer
        :type device_base_folder: str
        """
        self.tmp_dir = os.join(device_base_folder, 'filebridge.0000000001.2018_08_17_09_45_00_000')
        self.serializer = serializer
        self.connection = connection
        self.device_utils = DeviceUtils(connection)

    def send_data(self, data, path_on_device=None):
        """
        :type data: anything that the Serializer.serialize() can manage
        :type path_on_device: str
        :return:
        """
        if path_on_device is None:
            path_on_device = os.join(self.tmp_dir, '0000000353.2018_08_17_09_45_03_001')
        bytes = self.serializer.serialize(data)
        with self._tmp_file(bytes) as tmp_local_file:
            self._write_to_local_file(tmp_local_file, bytes)
            self.device_utils.push(tmp_local_file, path_on_device)
        return path_on_device

    def receive_data(self, path_on_device):
        """
        :type path_on_device: str
        :rtype output of Serializer.deserialize()
        """
        with self._tmp_file() as tmp_local_file:
            self.device_utils.pull(path_on_device, tmp_local_file)
            bytes = self._read_from_local_file(tmp_local_file)
        data = self.serializer.deserialize(bytes)
        return data

    # Other possible methods: send/receive_data_chunked, send/receive_file, send/receive_data_async,


#############################################


class LoopBackAppController:
    """
    example of app controller
    contains methods wrapping intents and commands
    that control a specific app on the device.
    decoupled from using this app to play audio data -
    this class has no knowledge of audio, or data

    it also is unique "per-app" and therefore does not have an interface
    """

    def __init__(self, connection, serializer, device_base_folder):
        self.device_base_folder = device_base_folder
        self.device_utils = DeviceUtils(connection)
        self.serializer = serializer

    def open_app(self):
        """
        send intent that opens the app
        :return:
        """
        pass

    def kill_app(self):
        """
        send intent that kills the app
        :return:
        """
        pass

    def play_file(self, path, with_record=False):
        """
        send intent for app to start playing
        :param path:
        :return:
        """
        return play_id

    def play_audio(self, song, with_record=False):
        with FileBridge(connection, self.serializer, self.device_base_folder) as data_bridge:
            data_to_send = self._prepare_to_send(song)

            send_file_handle = data_bridge.send(data_to_send)

            # validate send in some way
            self._check_send(send_file_handle)

            # send intent that starts to play
            play_id = self.play_file(send_file_handle.full_path, with_record)

            if (with_record):
                # the receive param may depend on the send params
                rcv_file_handle = self._make_rcv_handle(play_id)

                # Option 1 - you want to pull res all at once
                # wait for something
                self._wait_with_timeout(play_id)
                res = data_bridge.receive(rcv_file_handle)

                # Option 2 - chunked results
                # get data and do whatever with it
                for chunk in data_bridge.receive_chunked(rcv_file_handle):
                    yield chunk
                    if self._done(play_id):
                        break


class LoopbackAudioInterface:
    """
    example of how to use a data bridge and app controller
    to create an AI. both of these components can be replaced for
     testing, optimization, different hardwares, etc
    """

    def __init__(self, connection):
        self.connection = connection
        self.serializer = MySerialize()
        self.app_ctrl = LoopBackAppController(connection)
        self.device_base_folder = "my_folder"

    def _create_data_bridge(self):
        """
        mock this for testing, replace this for optimization, etc...
        :return:
        """
        return FileDataBridge(self.connection, self.serializer, self.device_base_folder)

    def record_and_play(self, song):
        for audio in self.app_ctrl.play_audio(song, with_record=True):
            self._process(audeio)
