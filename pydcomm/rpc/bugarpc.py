"""
This file defines the interface for RemoteProcedureCaller, which is to be implemented against each remote server.
The file also includes definitions and imports of all factories that create RemoteProcedureCallers.
Using RPC should be as simple as calling a factory and connecting to a remote server on the phone.

The file is meant to remain unchanged, except for the possible additions of factories at its bottom.
"""
from pydcomm.utils.userexpstats import metacollectstats


class IRemoteProcedureCaller(object):
    """
    This class represents a connection to a remote server that can execute certain procedures.
    Users must write their own "executors", but not their own server, see `bugarpc.h` for more details on the remote
    side.
    """
    __metaclass__ = metacollectstats

    def call(self, procedure_name, params):
        """
        Marshalls the params and sends them to the executor side. Then receives params that are returned from the
        executor and unmarshalls them.

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


class ICallerFactory(object):
    """
    Interface for factories creating remote procedure callers with a specific underlying technology.
    Factories must also implement two additional functionalities:
        1. `choose_device_id` - a user interface for selecting an available device_id.
        2. `install` - a function that installs a shared object file, that implements an executor for devices, on
                        a device, making it ready for connection.
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
        :rtype: IRemoteProcedureCaller
        """
        # if device_id is None:
        #     return cls.create_connection(rpc_id, device_id=cls.choose_device_id())

        raise NotImplementedError

    @classmethod
    def install(cls, so_path, device_id=None):
        # if device_id is None:
        #     return cls.install(so_path, device_id=cls.choose_device_id())
        raise NotImplementedError

    @classmethod
    def choose_device_id(cls):
        raise NotImplementedError


# region Factories
all_rpc_factories = {}
all_rpc_test_so = {}

# Define or import caller factories here.
#
# Every factory must also be associated with a compiled shared object file in the test-files repository that implements
# an executor and a function called `rpc_main`. This function must create an executor and a RPC server that starts
# listening on `rpc_id` 29999. The executor must respond to the procedure "dummy_send", which takes a single string
# as its arguments, and returns the same string with each byte increased by 1 modulo 256.


class DummyRemoteProcedureCaller(IRemoteProcedureCaller):
    def call(self, procedure_name, params):
        if procedure_name == "_rpc_get_version":
            return "1.0"
        elif procedure_name == "dummy_send":
            return "".join(chr((ord(c) + 1) % 256) for c in params)
        elif procedure_name == "_rpc_stop":
            return "stopped"
        else:
            raise ValueError("No such procedure name: {}".format(procedure_name))

    def get_version(self):
        return "1.0"


class DummyCallerFactory(ICallerFactory):
    @classmethod
    def create_connection(cls, rpc_id, device_id=None):
        assert device_id is None or device_id == "dummy", "Dummy device must have id dummy"
        return DummyRemoteProcedureCaller()

    @classmethod
    def install(cls, so_path, device_id=None):
        assert device_id is None or device_id == "dummy", "Dummy device must have id dummy"

    @classmethod
    def choose_device_id(cls):
        return "dummy"


all_rpc_factories["dummy"] = DummyCallerFactory
all_rpc_test_so["dummy"] = "dummy.so"

# endregion
