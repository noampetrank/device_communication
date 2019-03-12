# Define or import caller factories here.
#
# Every factory must also be associated with a compiled shared object file in the test-files repository that implements
# an executor and a function called `rpc_main`. This function must create an executor and a RPC server that starts
# listening on `rpc_id` 29999. The executor must respond to the procedure "dummy_send", which takes a single string
# as its arguments, and returns the same string with each byte increased by 1 modulo 256.

from collections import namedtuple
from pydcomm.connections.dummy import DummyRemoteProcedureClientFactory
from pydcomm.rpc.buga_grpc_client import GRpcSoLoaderLinuxClientFactory, GRpcSoLoaderAndroidClientFactory, GRpcLibbugatoneAndroidClientFactory

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

all_rpc_factories["grpc_soloader_linux"] = RpcFactoryEntry(GRpcSoLoaderLinuxClientFactory, "/home/buga/device_communication/cpp/lib/linux_x86/Release/libgrpc_test.so")
all_rpc_factories["grpc_soloader_apk_android"] = RpcFactoryEntry(GRpcSoLoaderAndroidClientFactory, "/home/buga/device_communication/cpp/lib/arm64/Release/libgrpc_test.so")

# all_rpc_factories["grpc_libbugatone_linux"] = RpcFactoryEntry(GRpcLibbugatoneLinuxClientFactory, "/home/buga/test-files/device_communication/resources/libbugatone_dummy.so.linux_x86.buga-recordings.c39f8e9fa34336b28a17b8713ff743f768d5a7d2")
all_rpc_factories["grpc_libbugatone_android"] = RpcFactoryEntry(GRpcLibbugatoneAndroidClientFactory, "/home/buga/test-files/device_communication/resources/libbugatone_dummy.so.arm64.buga-recordings.c39f8e9fa34336b28a17b8713ff743f768d5a7d2")
# all_rpc_factories["grpc_libbugatone_android"] = RpcFactoryEntry(GRpcLibbugatoneAndroidClientFactory, "/home/buga/mobileproduct/lib/arm64/Release/libbugatone_dummy.so")
