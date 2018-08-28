class RemoteProcedureCaller(object):
    def __init__(self, marshallers, unmarshallers):
        self.marshallers = marshallers
        self.unmarshallers = unmarshallers
        self.start()

    def call(self, procedure_name, explicit_marshallers=None, explicit_unmarshallers=None, **params):
        """
        Marshalls the params one-by-one and sends them to the callee side. Then receives params that are returned from the callee and unmarshalls them.
        :type procedure_name: str
        :type explicit_marshallers: dict[str: MarshallerBase subclass] or None
        :type explicit_unmarshallers: dict[str: UnmarshallerBase subclass] or None
        :type params: dict[str: marshallable]
        :param params: Can be any marshallable type, including generators that will be converted to streams.
        :return: Unmarshalled returned params (i.e. int, float, objects etc.)
        :rtype: dict[str: object]
        """
        marshalled_params = self._marshall(params, explicit_marshallers)
        ret = self._send_and_wait_for_return(procedure_name, marshalled_params)
        return self._unmarshall(ret, explicit_unmarshallers)

    def get_executor_version(self):
        ret_ver = self._send_and_wait_for_return('_rpc_get_version', {})
        return self._unmarshall(ret_ver, dict(version=VersionUnmarshaller))['version']

    def start(self):
        """
        Do whatever it takes to make the remote executor listen.
        """
        # ...
        xver = self.get_executor_version()
        # check if we can handle this executor version

    def stop(self):
        """
        Put the remote executor to bed.
        """
        pass

    def _marshall(self, params, explicit_marshallers):
        """
        Marshalls the params using self.marshallers (private method)
        :type params: dict[str: marshallable]
        :type explicit_marshallers: dict[str: MarshallerBase subclass] or None
        :return: dict[str: MarshalledObject]
        """
        pass

    def _unmarshall(self, params, explicit_unmarshallers):
        """
        Unmarshalls the params using self.unmarshallers (private method)
        :type params: dict[str: MarshalledObject]
        :type explicit_unmarshallers: dict[str: UnmarshallerBase subclass] or None
        :return: dict[str: marshallable]
        """
        pass

    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        raise NotImplementedError('This method needs to be overridden by subclass')




class AdbIntentsProcedureCaller(RemoteProcedureCaller):
    # This is an example for a specific implementation that uses ADB and intents to pass the calls.
    def __init__(self, marshallers, unmarshallers, connection, app_name):
        super(AdbIntentsProcedureCaller, self).__init__(marshallers, unmarshallers)
        self.connection = connection
        self.app_name = app_name

    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        pass



class MarshalledObject:
    def __init__(self):
        self.bytes = None
        self.attachments = {}



class MarshallerBase:
    def can_marshall(self, obj):
        pass

    def marshall(self, obj):
        pass


class UnmarshallerBase:
    def can_unmarshall(self, marshalled_object):
        pass

    def marshall(self, marshalled_object):
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
