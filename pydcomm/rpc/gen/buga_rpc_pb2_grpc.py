# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import buga_rpc_pb2 as buga__rpc__pb2


class DeviceRpcStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.call = channel.unary_unary(
        '/buga_rpc.DeviceRpc/call',
        request_serializer=buga__rpc__pb2.GRequest.SerializeToString,
        response_deserializer=buga__rpc__pb2.GResponse.FromString,
        )
    self.grpc_echo = channel.unary_unary(
        '/buga_rpc.DeviceRpc/grpc_echo',
        request_serializer=buga__rpc__pb2.GRequest.SerializeToString,
        response_deserializer=buga__rpc__pb2.GResponse.FromString,
        )


class DeviceRpcServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def call(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def grpc_echo(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_DeviceRpcServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'call': grpc.unary_unary_rpc_method_handler(
          servicer.call,
          request_deserializer=buga__rpc__pb2.GRequest.FromString,
          response_serializer=buga__rpc__pb2.GResponse.SerializeToString,
      ),
      'grpc_echo': grpc.unary_unary_rpc_method_handler(
          servicer.grpc_echo,
          request_deserializer=buga__rpc__pb2.GRequest.FromString,
          response_serializer=buga__rpc__pb2.GResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'buga_rpc.DeviceRpc', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))


class DeviceRpcStreamingStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.call = channel.unary_unary(
        '/buga_rpc.DeviceRpcStreaming/call',
        request_serializer=buga__rpc__pb2.GRequest.SerializeToString,
        response_deserializer=buga__rpc__pb2.GResponse.FromString,
        )
    self.call_streaming = channel.stream_stream(
        '/buga_rpc.DeviceRpcStreaming/call_streaming',
        request_serializer=buga__rpc__pb2.GBuffer.SerializeToString,
        response_deserializer=buga__rpc__pb2.GBuffer.FromString,
        )
    self.grpc_echo = channel.unary_unary(
        '/buga_rpc.DeviceRpcStreaming/grpc_echo',
        request_serializer=buga__rpc__pb2.GRequest.SerializeToString,
        response_deserializer=buga__rpc__pb2.GResponse.FromString,
        )
    self.grpc_echo_streaming = channel.stream_stream(
        '/buga_rpc.DeviceRpcStreaming/grpc_echo_streaming',
        request_serializer=buga__rpc__pb2.GBuffer.SerializeToString,
        response_deserializer=buga__rpc__pb2.GBuffer.FromString,
        )


class DeviceRpcStreamingServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def call(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def call_streaming(self, request_iterator, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def grpc_echo(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def grpc_echo_streaming(self, request_iterator, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_DeviceRpcStreamingServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'call': grpc.unary_unary_rpc_method_handler(
          servicer.call,
          request_deserializer=buga__rpc__pb2.GRequest.FromString,
          response_serializer=buga__rpc__pb2.GResponse.SerializeToString,
      ),
      'call_streaming': grpc.stream_stream_rpc_method_handler(
          servicer.call_streaming,
          request_deserializer=buga__rpc__pb2.GBuffer.FromString,
          response_serializer=buga__rpc__pb2.GBuffer.SerializeToString,
      ),
      'grpc_echo': grpc.unary_unary_rpc_method_handler(
          servicer.grpc_echo,
          request_deserializer=buga__rpc__pb2.GRequest.FromString,
          response_serializer=buga__rpc__pb2.GResponse.SerializeToString,
      ),
      'grpc_echo_streaming': grpc.stream_stream_rpc_method_handler(
          servicer.grpc_echo_streaming,
          request_deserializer=buga__rpc__pb2.GBuffer.FromString,
          response_serializer=buga__rpc__pb2.GBuffer.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'buga_rpc.DeviceRpcStreaming', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
