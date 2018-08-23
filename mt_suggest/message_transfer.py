class OldStyleAppController(object):
    def __init__(self, file_data_bridge, device_utils):
        self.file_data_bridge = file_data_bridge
        self.device_utils = device_utils

    def record_and_play(self, song):
        song_identifier = self.file_data_bridge.get_temp_path_on_device()
        recording_identifier = self.file_data_bridge.get_temp_path_on_device()

        song_identifier = self.file_data_bridge.send(song, song_identifier)
        message_id = self.device_utils.send_intent("record_and_play", song=song_identifier, times=100, volume=2)

        self.device_utils.wait_for_logcat("record_and_play", song=song_identifier, message_id=message_id)
        recording = self.file_data_bridge.receive_file(recording_identifier)
        return recording

    def do_synchronous_thing(self, some_parameter):
        message_id = self.device_utils.send_intent("something_with_result", p=some_parameter)
        response = self.device_utils.wait_for_logcat("record_and_play", message_id=message_id)
        return response


class NewStyleAppController(object):
    def __init__(self, message_transferrer):
        self.message_transferrer = message_transferrer

    def record_and_play(self, song):
        identifier = self.message_transferrer.send_message("record_and_play", song=song, times=100, volume=2)
        recording = self.message_transferrer.receive_message("record_and_play", id=identifier)
        return recording

    def do_synchronous_thing(self, some_parameter):
        return self.message_transferrer.send_message("something_with_result", p=some_parameter)


class AsyncStreamingAppController(object):
    def __init__(self, message_transferrer):
        self.message_transferrer = message_transferrer

    def record_and_play(self, song):
        identifier = self.message_transferrer.send_message_streaming("record_and_play", song=song, times=100, volume=2)
        return self.message_transferrer.receive_message_streaming("record_and_play", id=identifier)


class DeviceUtils(object):
    def logcat_wait_for_patterns(self, patterns):
        pass

    def get_logcat_iterator(self):
        pass

    def set_app_permissions(self):
        pass


class MessageTransFactory(object):
    def get_mt(self):
        cf = ConnectionFactory()
        con = cf.get_connected()
        mt = MessageTransferrer(con)
        return mt


class BaseMessageTransferrer(object):
    # Either pass an app parameter or the connection is to a specific app
    def send_message(self, message, **params):
        pass

    def receive_message(self, message, message_id):
        pass


class MessageTransferrer(object):
    def __init__(self, connection):
        self.connection = connection
        self.device_utils = DeviceUtils(connection)
        self.data_bridge = FileDataBridge(connection)

    def is_file(self, thing):
        pass

    def send_files(self, files):
        return [(pname, self.data_bridge.send_data(file)) for pname, file in files]

    def parse_return_value(self, row):
        # parse row
        # Pull fields mentioned in row
        pass

    # Either pass an app parameter or the connection is to a specific app
    def send_message(self, message, **params):
        message_id = 4
        files = [(n, p) for n, p in params if self.is_file(p)]
        identifiers = self.send_files(files, params)
        self.device_utils.send_intent(app, message, params + identifiers, message_id=message_id)
        return message_id

    def receive_message(self, message, message_id):
        return_value = self.device_utils.logcat_wait_for_patterns(app + message + message_id)
        return self.parse_return_value(return_value)


##########################33 JAVA

class KaddoshCommunicator(object):
    def __init__(self, connection_information):
        self.connection = SomeConnectionType(connection_information)  # adb (file path, intents name)/ socket (port)

    def register_listener(self, listener):
        msg = self.connection.receive_message()
        while msg:
            result = listener.dispatch(msg)
            self.connection.send_result(result, msg.message_id)
            msg = self.connection.receive_message()


class BaseListener(object):
    def dispatch(self, message):
        pass


class AudioInterfaceListener(BaseListener):
    def dispatch(self, message):
        if message.name == "record_and_play":
            return self.record_and_play(message.file, message.volume, message.times)
        if message.name == "notify_user":
            return self.notify_user(message=message.message)


class JavaAudioInterface(object):
    def __init__(self):
        # Java thing where you create a class in a class to create an observer
        com = KaddoshCommunicator(AudioInterfaceListener(self))

    def record_and_play(self):
        pass

    def notify_user(self):
        pass


class Message(object):
    def get_param(self, name, type):
        if type == "stream":
            return self.do_special_stream_stuff()
        return self.get("name")
