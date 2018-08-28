class RemoteProcedureCaller(object):
    def __init__(self):
        self.start()

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
        marshalled_params = marshaller(params) if marshaller else str(params)
        ret = self._send_and_wait_for_return(procedure_name, marshalled_params)
        return unmarshaller(ret) if unmarshaller else ret

    def get_executor_version(self):
        return self._send_and_wait_for_return('_rpc_get_version', {})

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

    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        raise NotImplementedError('This method needs to be overridden by subclass')


class UnsupportedExecutorVersion(Exception):
    pass


class ExecutorConnectionError(Exception):
    pass


def get_generator_marshaller(base_marshaller):
    """
    Converts a generator to a marshalled representation to be received as a stream on the executor side.
    :param base_marshaller: The marshaller to be used for the type returned by the generator.
    :type base_marshaller: function
    :return: A marshaller function that takes a generator and marshalls it for sending.
    :rtype: function
    """
    pass


def get_generator_unmarshaller(base_unmarshaller):
    """
    Converts a marshalled representation to a generator to read a stream sent from the executor side.
    :param base_unmarshaller: The unmarshaller to be used for the type returned by the generator.
    :type base_unmarshaller: function
    :return: An unmarshaller function that returns a generator by unmarshalling the received value.
    :rtype: function
    """
    pass
