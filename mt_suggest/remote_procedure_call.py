class RemoteProcedureCaller(object):
    def __init__(self, marshallers, unmarshallers):
        self.marshallers = marshallers
        self.unmarshallers = unmarshallers

    def call(self, procedure_name, **params):
        """
        Marshalls the params one-by-one and sends them to the callee side. Then receives params that are returned from the callee and unmarshalls them.
        :type procedure_name: str
        :type params: dict[str: marshallable]
        :param params: Can be any marshallable type, including generators that will be converted to streams.
        :return: Unmarshallod returned params
        :rtype: dict[str, object]
        """
        pass

    def _marshall(self, params):
        """
        Marshalls the params (protected method for subclasses)
        :type params: dict[str: marshallable]
        :return: dict[str: marshalled]
        """
        pass

    def _unmarshall(self, params):
        """
        Unmarshalls the params (protected method for subclasses)
        :type params: dict[str: marshalled]
        :return: dict[str: marshallable]
        """
        pass




class AdbIntentsProcedureCaller(RemoteProcedureCaller):
    # This is an example for a specific implementation that uses ADB and intents to pass the calls.
    def __init__(self, marshallers, unmarshallers, connection, app_name):
        super(AdbIntentsProcedureCaller, self).__init__(marshallers, unmarshallers)
        self.connection = connection
        self.app_name = app_name




class MarshallerBase:
    def can_marshall(self, obj):
        pass

    def marshall(self, obj):
        pass


class UnmarshallerBase:
    def can_unmarshall(self, bytes):
        pass

    def marshall(self, bytes):
        pass


# Generators can be marshalled and received as streams on the other side.
class GeneratorMarshaller(MarshallerBase):
    pass

class GeneratorUnmarshaller(UnmarshallerBase):
    pass








################### Ziv's code below ###################




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
        return_value = self.device_utils.logcat_wait_for_patterns(message + message_id)
        return self.parse_return_value(return_value)
