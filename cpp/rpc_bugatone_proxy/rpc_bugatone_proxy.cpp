#include <dlfcn.h>
#include <cstdio>
#include <thread>
#include "rpc_bindings/bugarpc.h"
#include "utils/rpc_log.h"

std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();

#ifdef __ANDROID__
#include <android/dlext.h>
#include <array>
#include <regex>

#define LIBBUGATONE_LOOKUP_PATHS {"libbugatone_real.so"};

int_between_30000_and_50000 get_requested_port() {
    //https://stackoverflow.com/a/478960/857731
    std::array<char, 128> buffer{0};
    std::string result;
    char cmd[4096];
    snprintf(cmd, sizeof(cmd), "getprop buga.rpc.libbugatone_executor_port");
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
    if (!pipe) {
        std::string err = "[RPCBugatoneProxy] Couldn't run getprop - popen() failed!";
        buga_rpc_log(err);
        throw std::runtime_error(err);
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    result = std::regex_replace(result, std::regex("\n"), "");
    int_between_30000_and_50000 ret = 0;
    try {
        ret = std::stoi(result);
    } catch (...) {
        std::string err = "[RPCBugatoneProxy] Wrong value received from getprop (" + result + "), stopping.";
        buga_rpc_log(err);
        throw std::runtime_error(err);
    }
    return ret;
}

#else
#include <cstdio>

#define LIBBUGATONE_LOOKUP_PATHS {"libbugatone.so"}

int_between_30000_and_50000 get_requested_port() {
    return 29999;
}

#endif


extern "C" void* _Z17createBugatoneApiv() {
    buga_rpc_log("[RPCBugatoneProxy] outer createBugatoneApi called");
    void* bugatoneApi = nullptr;

    void* myso = nullptr;
    const std::vector<const char*> libbugatone_paths = LIBBUGATONE_LOOKUP_PATHS;
    for (auto libbugatone_path : libbugatone_paths) {
        myso = dlopen(libbugatone_path, RTLD_LAZY);
        if (myso != nullptr) {
            buga_rpc_log(std::string("[RPCBugatoneProxy] *** loaded ") + libbugatone_path);
            break;
        }
    }
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
            createBugaGRPCServer()->listen(*executor, get_requested_port(), true);
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
