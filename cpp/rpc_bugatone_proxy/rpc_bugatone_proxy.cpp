#include <dlfcn.h>
#include <cstdio>
#include <thread>
#include "rpc_bindings/bugarpc.h"
#include "rpc_bindings/rpc_log.h"

std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();

#ifdef __ANDROID__
#include <android/dlext.h>

const char* libbugatone_path = "libbugatone_real.so";

#else
#include <cstdio>

const char* libbugatone_path = "/home/buga/mobileproduct/lib/linux_x86/Release/libbugatone.so";

#endif

extern "C" void* _Z17createBugatoneApiv() {
    buga_rpc_log("[RPCBugatoneProxy] outer createBugatoneApi called");
    void* bugatoneApi = nullptr;

    void* myso = dlopen(libbugatone_path, RTLD_NOW);
    if (myso == nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] failed to load .so");
        buga_rpc_log(dlerror());
        return bugatoneApi;
    }

    buga_rpc_log("[RPCBugatoneProxy] .so loaded");

    auto createBugatoneApi = (void* (*)())dlsym(myso, "_Z17createBugatoneApiv");
    if (createBugatoneApi == nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] symbol _Z17createBugatoneApiv not found, returning nullptr as bugatone api");
        buga_rpc_log(dlerror());
    } else {
        buga_rpc_log("[RPCBugatoneProxy] calling loaded createBugatoneApi");
        bugatoneApi = createBugatoneApi();
    }

    auto create_executor = (CreateExecutorFunc)dlsym(myso, "create_executor");
    if (create_executor != nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] creating gRPC thread");
        std::thread serverThread([create_executor] {
            buga_rpc_log("[RPCBugatoneProxy] gRPC thread started, calling create_executor");
            std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
            buga_rpc_log("[RPCBugatoneProxy] calling listen");
            createBugaGRPCServer()->listen(*executor, 30000, true);
            buga_rpc_log("[RPCBugatoneProxy] gRPC server listen done, thread returning");
        });
        buga_rpc_log("[RPCBugatoneProxy] detaching gRPC server thread");
        serverThread.detach();
    } else {
        buga_rpc_log("[RPCBugatoneProxy] symbol create_executor not found");
        buga_rpc_log(dlerror());
    }

    return bugatoneApi;
}