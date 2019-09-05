import grpc
from concurrent import futures
from pydcomm.rpc.gen.buga_rpc_pb2_grpc import (DeviceRpcStub, DeviceRpcServicer, add_DeviceRpcServicer_to_server, 
                                               DeviceRpcStreamingStub, DeviceRpcStreamingServicer, 
                                               add_DeviceRpcStreamingServicer_to_server)
from pydcomm.rpc.gen.buga_rpc_pb2 import GRequest, GResponse
from pydcomm.rpc.buga_grpc_client import GRemoteProcedureClient, ReaderWriterStream
from pydcomm.rpc.common import GReaderWriterStream

from pybuga.infra.utils.thread_utils import apply_async

class RemoteProcedureExecutor(object):
    def execute_procedure(self, procedure_name, params):
        """
        This method will be called by the RemoteProcedureServer on each sent message.

        Notes:
          Procedure names beginning with "_rpc_" are reserved for server implementers, and therefore must not be used.

        @param str procedure_name: Name of procedure called, not beginning with "_rpc_".
        @param str params: The Buffer sent from python.
        @return: Buffer representing return value to be sent back to python.
        @rtype: str
        """
        raise NotImplementedError
        
    def get_version(self):
        """
        @return: String representing the version of the executor.
        @rtype: str
        """
        raise NotImplementedError

class RemoteProcedureStreamingExecutor(RemoteProcedureExecutor):
    """
    This method will be called by the RemoteProcedureStreamingServer.
    The method return an iterbale or be a generator. Each yielded value will
    be written back to the caller. Use the `it` argument to read values
    written by the caller.
    """
    def execute_streaming_procedure(self, procedure_name, params, it):
        raise NotImplementedError

class RemoteProcedureServer(object):
    """
    Public interface to RPC servers. This is implemented by the library owners and used by the library clients.

    All server implementations have the following requirements:
        1. If python calls the procedure "_rpc_get_version", server must call `getVersion` on the executor
            instance and return the result.
        2. If python calls the procedure "_rpc_stop", server must call its `stop` method.
    """
    def listen(self, executor, rpc_id, wait):
        """
        Start listening on given port to messages from python and pass them along to the executor.
        
        @param RemoteProcedureExecutor listener: Executor implementation that responds to messages.
        @param int rpc_id: Unique identifier for your executor to listen to, must be between 30,000 and 50,000.
        @param bool wait: Whether to block waiting or to return immediately. It this is false, 
            you need to call wait() later on.
        """
        raise NotImplementedError
        
    def wait(self):
        """
        Block waiting in a server loop. This should be used if listen() was called with wait==false.
        Could be from a different thread than listen().
        """
        raise NotImplementedError
        
    def stop(self):
        """
        Stop listening, makes the listen thread return.
        """
        raise NotImplementedError
        
class RemoteProcedureStreamingServer(object):
    """
    Start listening on given port to calls from python. Each call will trigger calling
    `executor.execute_streaming_procedure`.
    """
    def listen_streaming(self, executor, rpc_id, wait):
        raise NotImplementedError


class BugaGRpcServiceImpl(DeviceRpcServicer):
    """A python version of the C++ class of the same name"""
    def __init__(self, executor, stop_func):
        self.executor = executor
        self.stop_func = stop_func
        
    def call(self, request, context):
        procedure_name = request.name
        params = request.buf
        
        if procedure_name == "_rpc_get_version":
            ret = self.executor.get_version()
        elif procedure_name == "_rpc_device_time_usec":
            import time
            ret = str(time.time() * 1000)
        elif procedure_name == "_rpc_stop":
            self.stop_func()
            ret = ""
        else:
            ret = self.executor.execute_procedure(procedure_name, params)
        
        return GResponse(buf=ret)
    
    def grpc_echo(self, request, context):
        return GResponse(buf="hmm?")


class BugaGRpcStreamingServiceImpl(BugaGRpcServiceImpl, DeviceRpcStreamingServicer):
    def call_streaming(self, request_iterator, context):
        from itertools import imap

        procedure_name = next(request_iterator).buf
        params = next(request_iterator).buf

        bufs = imap(lambda _: _.buf, request_iterator)

        for value in self.executor.execute_streaming_procedure(procedure_name, params, bufs):
            yield GResponse(buf=value)

    
class GRemoteProcedureServer(RemoteProcedureServer):
    """
    A remote procedure server implementation that uses gRPC
    
    This is a python version of the C++ class of the same name.
    """
    def __init__(self, max_workers=10, wait_sleep=0):
        self.max_workers = max_workers
        self.wait_sleep = wait_sleep
        self.server = None

    def _add_servicer_to_server(self, server, executor):
        add_DeviceRpcServicer_to_server(BugaGRpcServiceImpl(executor, self.stop), server)
        
    def listen(self, executor, rpc_id, wait):
        self.server = server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.max_workers))
        self._add_servicer_to_server(server, executor)
        ret = server.add_insecure_port('[::]:{}'.format(rpc_id))
        if ret == 0:
            raise RuntimeError("Cannot bind to port {}".format(rpc_id))
        server.start()
        if wait:
            self.wait()
    
    def wait(self):
        import time
        stage = self.server._state.stage
        while stage != stage.STOPPED:
            time.sleep(self.wait_sleep)
            
    def stop(self, timeout=None):
        """
        Try to stop server with a timeout.
        
        @return: Whether the stop definitely happened.
        @rtype: bool
        """
        assert self.server, "No server set"
        return self.server.stop(0).wait(timeout)
    
class GRemoteProcedureStreamingServer(RemoteProcedureStreamingServer, GRemoteProcedureServer):
    listen_streaming = GRemoteProcedureServer.listen
    
    def _add_servicer_to_server(self, server, executor):
        add_DeviceRpcStreamingServicer_to_server(BugaGRpcStreamingServiceImpl(executor, self.stop), server)

class BugaEchoExecutor(RemoteProcedureExecutor):
    """A simple echo executor"""
    def execute_procedure(self, procedure_name, params):
        return params
    
    def get_version(self):
        return "1.0"

class BugaEchoStreamingExecutor(BugaEchoExecutor, RemoteProcedureStreamingExecutor):
    def execute_streaming_procedure(self, procedure_name, params, it):
        yield "{}:{}".format(procedure_name, params)
        for value in it:
            yield value



class Call(object):
    """
    Object representing a call to an executor
    Use `return_` to set the return value, after which the rpc call returns to its caller.
    """
    def __init__(self, ret_event, index, procedure_name, params):
        self._ret_event = ret_event  # type: threading.Event
        self.index = index  # type: int
        self.procedure_name = procedure_name  # type: str
        self.params = params  # type: str
        self.returned = False
        self.return_value = None  # type: None or str
        
    def return_(self, value):
        """Set the return value of this call"""
        assert not self._ret_event.is_set(), "Call already returned"
        self.return_value = value
        self.returned = True
        self._ret_event.set()
        
    def __str__(self):
        if self.returned:
            return_value = "\nreturn value={!r}".format(self.return_value)
        else:
            return_value = ""
        return """Call:
index={}
returned={}
procedure_name={!r}
params={!r}{}""".format(self.index, self.returned, self.procedure_name, self.params, return_value)
    
    def __repr__(self):
        return "Call(index={}, returned={}, procedure_name={})".format(self.index, self.returned, self.procedure_name)
    
class AsyncExecutor(RemoteProcedureExecutor):
    """
    An asynchronous executor that lets users take their time to reply to calls
    
    Calls waiting for an answer are stored in `waiting_calls`, indexed by incoming order.
    Calls that have been answered are stored in `logged_calls`, ordered by return time.
    A user may choose to reply to incoming calls in a different order, and this will be reflected in `logged_calls`,
    and each stored `Call` instance retains its original incoming index as a member, available for inspection.
    
    Use `get()` to get the top most waiting call. Throws `StopIteration` if the waiting list is empty.
    Use `empty()` to check if there's a call waiting.
    """
    def __init__(self, verbose=True):
        from threading import Lock
        from collections import OrderedDict
        
        self.index = 0
        self.lock = Lock()
        self.waiting_calls = OrderedDict()
        self.logged_calls = []
        self.verbose = verbose
        
    def execute_procedure(self, procedure_name, params):
        from threading import Event
        
        ret_event = Event()
        
        with self.lock:
            index = self.index
            self.index += 1
            self.waiting_calls[index] = call = Call(ret_event, index, procedure_name, params)
            
        if self.verbose:
            print "[AsyncExecutor] incoming {!r}".format(call)
            
        ret_event.wait()
        
        with self.lock:
            del self.waiting_calls[index]
            self.logged_calls.append(call)
            
        if self.verbose:
            print "[AsyncExecutor] returning on call: {}".format(index)
        
        return call.return_value
    
    def get(self):
        """Get the top most waiting call. Throws `StopIteration` if the waiting list is empty."""
        with self.lock:
            index = next(iter(self.waiting_calls))
            return self.waiting_calls[index]
    
    def empty(self):
        """Check if there's a call waiting."""
        return len(self.waiting_calls) == 0
        
    def get_version(self):
        return "1.0"
    
class AsyncServerAndExecutor(object):
    def __init__(self, port, server=None, verbose=True):
        """
        Conveniance object putting server and executor in one object
        If server is None, uses GRemoteProcedureServer (gRPC).
        
        @param int port: Port to listen on.
        @param RemoteProcedureServer server: Server instance for running the executor. Must not have started yet.
        @param bool verbose: Whether to print when calls come in and when they are returned.
        """
        self.port = port
        if server is None:
            server = GRemoteProcedureServer()
        self.server = server
        self.async_executor = AsyncExecutor(verbose)
        
    def start(self):
        """Start listening on port."""
        self.server.listen(self.async_executor, self.port, False)
        
    def __enter__(self):
        self.start()
        return self
    
    def stop(self, timeout=None):
        """Stop server with timeout. Returns if server definitely stopped."""
        return self.server.stop(timeout)
        
    def __exit__(self, *args):
        self.stop(10)
        
    def empty(self):
        """Check if there's a call waiting."""
        return self.async_executor.empty()
    
    def get(self):
        """Get the top most waiting call. Throws `StopIteration` if the waiting list is empty."""
        return self.async_executor.get()
    
    @property
    def waiting_calls(self):
        """Get `OrderedDict` of waiting calls. Careful, this is used in multiple threads."""
        return self.async_executor.waiting_calls
    
    @property
    def logged_calls(self):
        """Get log of returned calls. Careful, this is used in multiple threads."""
        return self.async_executor.logged_calls