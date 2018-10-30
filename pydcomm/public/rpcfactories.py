# Define or import caller factories here.
#
# Every factory must also be associated with a compiled shared object file in the test-files repository that implements
# an executor and a function called `rpc_main`. This function must create an executor and a RPC server that starts
# listening on `rpc_id` 29999. The executor must respond to the procedure "dummy_send", which takes a single string
# as its arguments, and returns the same string with each byte increased by 1 modulo 256.

from collections import namedtuple
from pydcomm.connections.dummy import DummyRemoteProcedureClientFactory
from pydcomm.rpc.buga_grpc_client import GRemoteProcedureClientFactory

RpcFactoryEntry = namedtuple("RpcFactoryEntry", "factory_cls test_so")

# noinspection PyDictCreation
all_rpc_factories = {}

#
# Example:
#   class MyCallerFactory(ICallerFactory):
#       ...
#
#   all_rpc_factories["mine"] = RpcFactoryEntry(MyCallerFactory, "minecaller1.so")
#

all_rpc_factories["dummy"] = RpcFactoryEntry(DummyRemoteProcedureClientFactory, "dummy.so")
all_rpc_factories["grpc"] = RpcFactoryEntry(GRemoteProcedureClientFactory, "/home/buga/device_communication/cpp/lib/linux_x86/Release/libgrpc_test.so")
