"""
This file defines the interface for RemoteProcedureCaller, which is to be implemented against each remote server.
The file also includes definitions and imports of all factories that create RemoteProcedureCallers.
Using RPC should be as simple as calling a factory and connecting to a remote server on the phone.

The file is meant to remain unchanged, except for the possible additions of factories at its bottom.
"""
from pydcomm.utils.userexpstats import metacollectstats


class IRemoteProcedureCaller:
    """
    This class represents a connection to a remote server that can execute certain procedures.
    Users must write their own "executors", but not their own server, see `bugarpc.h` for more details on the remote
    side.
    """
    __metaclass__ = metacollectstats

    def call(self, procedure_name, params, marshaller=None, unmarshaller=None):
        """
        Marshalls the params and sends them to the executor side. Then receives params that are returned from the
        executor and unmarshalls them.

        :type procedure_name: str
        :type params: marshallable
        :param params: Can be any type marshallable by the marshaller, possibly generators that will be converted to
        streams on the executor.
        :type marshaller: function or None
        :type unmarshaller: function or None
        :return: Unmarshalled returned params (i.e. float, dict, object etc.)
        :rtype: dict[str: object]
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
        return self.call("_rpc_get_version", {})


class ICallerFactory:
    """

    """
    __metaclass__ = metacollectstats

    @classmethod
    def create_connection(cls, port, device_id=None):
        """
        Creates an rpc object. User must take care to connect.

        :return: A RemoteProcedureCaller.
        :rtype: IRemoteProcedureCaller
        """
        if device_id is None:
            return cls.create_connection(port, cls.choose_device_id())

        raise NotImplementedError

    @classmethod
    def choose_device_id(cls):
        raise NotImplementedError

    @classmethod
    def install(cls, so_path):
        raise NotImplementedError


# region Factories

# Define or import caller factories here.

# endregion
