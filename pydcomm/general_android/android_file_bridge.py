import os


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
        return str(data)

    def deserialize(self, buffer):
        """
        turn bytes into data
        :type buffer: binary data
        :return:
        """
        return buffer


class FileBridge:
    def __init__(self, device_utils, serializer, device_base_folder='/sdcard/tmp/'):
        """
        :type device_utils: AndroidDeviceUtils
        :type serializer: Serializer
        :type device_base_folder: str
        """
        self.tmp_dir = self._make_tmp_dir_path(device_base_folder)
        self.serializer = serializer
        self.device_utils = device_utils

    def send_data(self, data, path_on_device=None):
        """
        :type data: anything that the Serializer.serialize() can manage
        :type path_on_device: str
        :return:
        """
        if path_on_device is None:
            path_on_device = self._make_tmp_file_path()
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
        with self._tmp_local_file() as tmp_local_file:
            self.device_utils.pull(path_on_device, tmp_local_file)
            bytes = self._read_from_local_file(tmp_local_file)
        data = self.serializer.deserialize(bytes)
        return data

    def _make_tmp_dir_path(self, base_folder):
        return os.join(base_folder, 'filebridge.0000000001.2018_08_17_09_45_00_000')

    def _make_tmp_file_path(self, dir_path=None):
        dir_path = dir_path or self.tmp_dir
        return os.join(dir_path, "0000000353.2018_08_17_09_45_03_001")

    def _tmp_local_file(self):
        """
        :return: A context that returns a path string and deletes the file in the end
        """
        pass

    # Other possible methods: send/receive_data_chunked, send/receive_file, send/receive_data_async,
