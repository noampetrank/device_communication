from abc import ABCMeta, abstractmethod


class IRemoteProcedureCaller:
    __metaclass__ = ABCMeta

    @abstractmethod
    def call(self, procedure_name, params, marshaller=None, unmarshaller=None):
        """
        Marshalls the params and sends them to the executor side. Then receives params that are returned from the executor and unmarshalls them.
        :type procedure_name: str
        :type params: marshallable
        :param params: Can be any type marshallable by the marshaller, possibly generators that will be converted to streams on the executor.
        :type marshaller: function or None
        :type unmarshaller: function or None
        :return: Unmarshalled returned params (i.e. float, dict, object etc.)
        :rtype: dict[str: object]
        """
        pass

    @abstractmethod
    def get_executor_version(self):
        """
        Returns the version string of the executor.
        :rtype: str
        """

    @abstractmethod
    def start(self):
        """
        Do whatever it takes to make the remote executor listen.
        :rtype: None
        """

    @abstractmethod
    def stop(self):
        """
        Put the remote executor to bed.
        :rtype: None
        """
        pass


class StandardRemoteProcedureCaller(IRemoteProcedureCaller):
    def call(self, procedure_name, params, marshaller=None, unmarshaller=None):
        marshalled_params = marshaller(params) if marshaller else str(params)
        ret = self._send_and_wait_for_return(procedure_name, marshalled_params)
        return unmarshaller(ret) if unmarshaller else ret

    def get_executor_version(self):
        return self._send_and_wait_for_return('_rpc_get_version', '')

    def start(self):
        # ...
        xver = self.get_executor_version()
        # check if we can handle this executor version

    def stop(self):
        pass

    @abstractmethod
    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        """
        Specific implementation that calls a procedure on the executor and returns values from it.
        :param procedure_name:
        :param marshalled_params:
        :return:
        """
        pass


class UnsupportedExecutorVersion(Exception):
    pass


class ExecutorConnectionError(Exception):
    pass


# TODO add streaming API