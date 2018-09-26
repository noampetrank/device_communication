gRPC on Android
===============

This folder contains two projects:

**bugarpc** - an Android library that provides JNI bindings to a gRPC implementation
of the Bugatone RPC interface. 

**echo** - an Android app that runs a gRPC server on a given port and responds to
calls with echo. Depends on the bugarpc library.


You can use the echo project as reference or starting point to build an Android gRPC server.\
To implement your executor, 
- Implement the `BugaRpcExecutor` interface
- Register it with the server using `BugaGrpc.registerExecutor`
- Start the server using `startServer`
- Refer to `CMakeLists.txt` for compilation.


The user can communicate with the gRPC server from Python using a BugaGRpcCaller object:
```python
from pydcomm.rpc.buga_grpc_caller import BugaGRpcCaller
caller = BugaGRpcCaller(host_port)
caller.start()

caller.call('_rpc_echo', 'Hey there!')
caller.call('method_on_device', params_object, marshaller_for_params, unmarshaller_for_return_value)

# Run benchmark
from pydcomm.benchmarks.rpc_benchmarks import call_benchmark
call_benchmark(caller, compare_to_adb=True)

# Finish
caller.stop()
```


PREREQUISITES
-------------

- Android SDK
- Android NDK
- `protoc` and `grpc_cpp_plugin` binaries on the host system


INSTALL
-------

The example application can be built via Android Studio or on the command line
using `gradle`:

```sh
$ ./gradlew installDebug
```


_Note:_ Building the protobuf dependency for Android requires
https://github.com/google/protobuf/pull/3878. This fix will be in the next
protobuf release, but until then must be manually patched in to
`third_party/protobuf` to build gRPC for Android. This is why we forked the
grpc and protobug projects.
