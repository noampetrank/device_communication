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


class NewStyleAudioInterface(object):
    def __init__(self, message_transport):
        self.message_transport = message_transport
    def record_and_play(self, song):
        """
        Plays song and records. Returns recording (loopback + recording).
        """
        try:
            ret_bytes = self.message_transport.send_message("record_and_play", song=song, times=100, volume=2)
            return convert_to_numpy(ret_bytes)
        except MessageTransportError as exc:
            print "bummer", exc
            return None

class StreamingNewStyleAudioInterface(object):
    def play_internet_radio(self):
        generator = IteratorToStream((x for x in readRadioFromInternet()))
        for resp in self.message_transport.send_message("record_and_play_streaming", generator):
            print echo_analyzer.next(resp).temperature

    def record_and_play_stream(self, song):
        res = self.message_transport.send_message("record_and_play_stream", song=song, times=100, volume=2)
        return res

"""
In json, stream serializes to:

{
    type: "Stream<byte[]>",
    port: 1872
}
"""
