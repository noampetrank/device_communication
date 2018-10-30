#include <dlfcn.h>
#include <cstdio>
#include <thread>
#include "rpc_bindings/bugarpc.h"

std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();

#ifdef __ANDROID__
#include <android/dlext.h>
#include <android/log.h>
#define myputs(msg) __android_log_print(ANDROID_LOG_INFO, "Bugatone", "%s", msg)

const char* libbugatone_path = "libbugatone_real.so";

#else
#include <cstdio>
#define myputs(msg) std::puts(msg)

const char* libbugatone_path = "/home/buga/mobileproduct/lib/linux_x86/Release/libbugatone.so";

#endif

extern "C" void* _Z17createBugatoneApiv() {
    myputs("[RPCBugatoneProxy] outer createBugatoneApi called");
    void* bugatoneApi = nullptr;

    void* myso = dlopen(libbugatone_path, RTLD_NOW);
    if (myso == nullptr) {
        myputs("[RPCBugatoneProxy] failed to load .so");
        myputs(dlerror());
        return bugatoneApi;
    }

    myputs("[RPCBugatoneProxy] .so loaded");

    auto createBugatoneApi = (void* (*)())dlsym(myso, "_Z17createBugatoneApiv");
    if (createBugatoneApi == nullptr) {
        myputs("[RPCBugatoneProxy] symbol _Z17createBugatoneApiv not found, returning nullptr as bugatone api");
        myputs(dlerror());
    } else {
        myputs("[RPCBugatoneProxy] calling loaded createBugatoneApi");
        bugatoneApi = createBugatoneApi();
    }

    auto create_executor = (CreateExecutorFunc)dlsym(myso, "create_executor");
    if (create_executor != nullptr) {
        myputs("[RPCBugatoneProxy] creating gRPC thread");
        std::thread serverThread([create_executor] {
            myputs("[RPCBugatoneProxy] gRPC thread started, calling create_executor");
            std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
            myputs("[RPCBugatoneProxy] calling listen");
            createBugaGRPCServer()->listen(*executor, 30000, true);
            myputs("[RPCBugatoneProxy] gRPC server listen done, thread returning");
        });
        myputs("[RPCBugatoneProxy] detaching gRPC server thread");
        serverThread.detach();
    } else {
        myputs("[RPCBugatoneProxy] symbol create_executor not found");
        myputs(dlerror());
    }

    return bugatoneApi;
}