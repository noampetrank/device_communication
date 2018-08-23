class IteratorToStream(object):
    """This class does some magic so we can send generators through the MessageTransport"""
    pass

class MessageTransportError(Exception):
    pass

class MessageTransFactory(object):
    def get_message_transport(self):
        cf = ConnectionFactory()
        con = cf.get_connected()
        mt = MessageTransport(con)
        return mt


class BaseMessageTransport(object):
    # Either pass an app parameter or the connection is to a specific app
    def send_message(self, message, **params):
        pass

    def receive_message(self, message, message_id):
        pass


class AdbIntentsMessageTransport(object):
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
        identifiers = self.send_files(files)
        self.device_utils.send_intent(message, params + identifiers, message_id=message_id)
        return message_id

    def receive_message(self, message, message_id):
        return_value = self.device_utils.logcat_wait_for_patterns(message + message_id)
        return self.parse_return_value(return_value)
