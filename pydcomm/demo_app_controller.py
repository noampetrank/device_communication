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
        return FileBridge(self.connection, self.serializer, self.device_base_folder)

    def record_and_play(self, song):
        for audio in self.app_ctrl.play_audio(song, with_record=True):
            self._process(audio)

# endregion
