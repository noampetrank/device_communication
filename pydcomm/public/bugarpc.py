"""
This file defines the interface for RemoteProcedureClient, which is to be implemented against each remote server.
The file also includes definitions and imports of all factories that create RemoteProcedureClients.
Using RPC should be as simple as calling a factory and connecting to a remote server on the phone.

The file is meant to remain unchanged, except for the possible additions of factories at its bottom.
"""
from pydcomm.public.ux_stats import metacollectstats


class IRemoteProcedureClient(object):
    """
    This class represents a connection to a remote server that can execute certain procedures.
    Users must write their own "executors", but not their own server, see `bugarpc.h` for more details on the remote
    side.
    """
    __metaclass__ = metacollectstats

    def call(self, procedure_name, params):
        """
        Calls procedure on device with the params.

        :param str procedure_name: Name of procedure that device side handles.
        :param str params: String, equivalently bytes, to send.
        :return: String sent from device.
        :rtype: str
        """
        raise NotImplementedError

    def get_version(self):
        """
        Returns the version string of this class.
        :rtype: str
        """
        raise NotImplementedError

    def get_executor_version(self):
        """
        :return: Returns the version string of the remote executor.
        """
        return self.call("_rpc_get_version", "")


class ReaderWriterStream(object):
    """
    Interface for return object from a streaming call.
    Member functions:
        read, write, end_write
    """
    def read(self):
        """
        Receive value from server side.

        This is blocking until server sends a response, or closes the connection.
        """
        raise NotImplementedError

    def write(self, value):
        """Write a value to the server."""
        raise NotImplementedError

    def end_write(self):
        """Tell server that you're done writing."""
        raise NotImplementedError


class IRemoteProcedureStreamingClient(object):
    __metaclass__ = metacollectstats

    def call_streaming(self, procedure_name, params):
        """
        Calls a streaming procedure with the params, and returns an iterator of streamed resuls.

        :param str procedure_name: Name of procedure that device side handles.
        :param str params: String to send.
        :return: Iterator of streamed results from device.
        :rtype: ReaderWriterStream
        """
        raise NotImplementedError


class IRemoteProcedureClientFactory(object):
    """
    Interface for factories creating remote procedure callers with a specific underlying technology.
    Factories must also implement two additional functionalities:
        1. `choose_device_id` - a user interface for selecting an available device_id.
        2. `install_executor` - a function that installs a shared object file, that implements an executor for devices,
                        on a device, making it ready for connection.
    """
    __metaclass__ = metacollectstats

    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        """
        Creates a remote procedure caller and connects to the device. If no device is given, this function must call
        the class's `choose_device_id` method.

        In order to be able to run multiple executors on a device, each caller-executor pair is assigned an `rpc_id` -
        a whole number in the range 30,000 - 50,000. Python and C++ implementations must take care to connect to and
        listen for the same id.

        :param int rpc_id: Id of caller-executor pair, a whole number between 30,000 - 50,000.
        :param str|None device_id: String representing device id or None. If None then `choose_device_id` is called.
        :return: A RemoteProcedureCaller.
        :rtype: IRemoteProcedureClient
        """
        # if device_id is None:
        #     return cls.create_connection(rpc_id, device_id=cls.choose_device_id())

        raise NotImplementedError

    @classmethod
    def install_executor(cls, so_path, rpc_id, device_id=None):
        # if device_id is None:
        #     return cls.install_executor(so_path, device_id=cls.choose_device_id())
        raise NotImplementedError

    @classmethod
    def choose_device_id(cls):
        raise NotImplementedError


class RpcError(RuntimeError):
    """
    This is an exception that is thrown upon errors regarding RPC.
    """
    def __init__(self, *args, **kwargs):
        """
        :param grpc_exception: the original grpc exception, if this originated from gRPC code.
        """
        self.grpc_exception = kwargs.pop('grpc_exception', None)
        super(RpcError, self).__init__(args, kwargs)

    def __str__(self):
        return super(RpcError, self).__str__() + "\nOriginal gRPC exception: " + repr(self.grpc_exception)
