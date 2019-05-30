#include <dlfcn.h>
#include <cstdio>
#include <thread>
#include "rpc_bindings/bugarpc.h"
#include "utils/rpc_log.h"

std::unique_ptr<IRemoteProcedureStreamingServer> createBugaGRPCStreamingServer();
std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();

#ifdef __ANDROID__
#include <android/dlext.h>
#include <array>
#include <regex>

#define LIBBUGATONE_LOOKUP_PATHS {"libbugatone_real.so"};

int_between_30000_and_50000 get_requested_port() {
    try {
        //https://stackoverflow.com/a/478960/857731
        std::array<char, 128> buffer{0};
        std::string result;
        char cmd[4096];
        snprintf(cmd, sizeof(cmd), "getprop buga.rpc.libbugatone_executor_port");
        buga_rpc_log("Running " + std::string(cmd) + "...");
        std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
        if (!pipe) {
            std::string err = "[RPCBugatoneProxy] Couldn't run getprop - popen() failed!";
            buga_rpc_log(err);
            throw std::runtime_error(err);
        }
        while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
            result += buffer.data();
        }
        buga_rpc_log(std::string(cmd) + " returned value of " + result);
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
    } catch(const std::exception& e) {
        return 44444;
    }
}

#else
#include <cstdio>

#ifndef IS_AUTHDEMO
#define LIBBUGATONE_LOOKUP_PATHS {"libbugatone.so"}
#else
#define LIBBUGATONE_LOOKUP_PATHS {"libauthdemo.so"}
#endif

int_between_30000_and_50000 get_requested_port() {
    return 29999;
}

#endif


extern "C" void* _Z17createBugatoneApiv() {
    buga_rpc_log("[RPCBugatoneProxy] outer createBugatoneApi called");
    void* bugatoneApi = nullptr;
    std::unique_ptr<IRemoteProcedureStreamingExecutor> streaming_executor = nullptr;
    std::unique_ptr<IRemoteProcedureExecutor> executor = nullptr;

    void* myso = nullptr;
    const std::vector<const char*> libbugatone_paths = LIBBUGATONE_LOOKUP_PATHS;
    for (auto libbugatone_path : libbugatone_paths) {
        buga_rpc_log("[RPCBugatoneProxy] trying to load: " + std::string(libbugatone_path));
        myso = dlopen(libbugatone_path, RTLD_LAZY);
        if (myso != nullptr) {
            buga_rpc_log(std::string("[RPCBugatoneProxy] *** loaded ") + libbugatone_path);
            break;
        }
    }
    if (myso == nullptr) {
        buga_rpc_log(dlerror());
        buga_rpc_log("[RPCBugatoneProxy] failed to load .so");
        return bugatoneApi;
    }
    buga_rpc_log("[RPCBugatoneProxy] .so loaded");

    using CreateStreamingPairFunc = std::pair<void*, std::unique_ptr<IRemoteProcedureStreamingExecutor>> (*)();
    using CreatePairFunc = std::pair<void*, std::unique_ptr<IRemoteProcedureExecutor>> (*)();

    auto create_streaming_pair = (CreateStreamingPairFunc)dlsym(myso, "create_bugatoneapi_and_streaming_executor");
    if (create_streaming_pair != nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] calling loaded create_bugatoneapi_and_streaming_executor");
        auto pair = create_streaming_pair();
        bugatoneApi = pair.first;
        streaming_executor = std::move(pair.second);
    } else {
        buga_rpc_log(dlerror());
        buga_rpc_log("[RPCBugatoneProxy] symbol create_bugatoneapi_and_streaming_executor not found, trying to load create_bugatoneapi_and_executor instead");

        auto create_pair = (CreatePairFunc)dlsym(myso, "create_bugatoneapi_and_executor");
        if (create_pair != nullptr) {
            buga_rpc_log("[RPCBugatoneProxy] calling loaded create_bugatoneapi_and_executor");
            auto pair = create_pair();
            bugatoneApi = pair.first;
            executor = std::move(pair.second);
        } else {
            buga_rpc_log(dlerror());
            buga_rpc_log("[RPCBugatoneProxy] symbol create_bugatoneapi_and_executor not found, trying to load create_executor and _Z17createBugatoneApiv instead");

            auto create_executor = (CreateExecutorFunc)dlsym(myso, "create_executor");
            if (create_executor != nullptr) {
                buga_rpc_log("[RPCBugatoneProxy] calling loaded create_executor");
                executor = create_executor();
            } else {
                buga_rpc_log(dlerror());
                buga_rpc_log("[RPCBugatoneProxy] symbol create_executor not found, not starting gRPC");
            }

            auto createBugatoneApi = (void* (*)())dlsym(myso, "_Z17createBugatoneApiv");
            if (createBugatoneApi != nullptr) {
                buga_rpc_log("[RPCBugatoneProxy] calling loaded createBugatoneApi");
                bugatoneApi = createBugatoneApi();
            } else {
                buga_rpc_log(dlerror());
                buga_rpc_log("[RPCBugatoneProxy] symbol _Z17createBugatoneApiv not found, returning nullptr as bugatone api");
                if (executor != nullptr) {
                    buga_rpc_log("[RPCBugatoneProxy] not starting gRPC since no bugatone api was created");
                }
            }
        }
    }

    if (streaming_executor != nullptr && bugatoneApi != nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] creating gRPC thread");
        std::thread serverThread([executor=std::move(streaming_executor)] {
            buga_rpc_log("[RPCBugatoneProxy] gRPC thread started");  // , calling create_executor");
            // std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
            buga_rpc_log("[RPCBugatoneProxy] calling listen");
            createBugaGRPCStreamingServer()->listenStreaming(*executor, get_requested_port(), true);
            buga_rpc_log("[RPCBugatoneProxy] gRPC server listen done, thread returning");
        });
        buga_rpc_log("[RPCBugatoneProxy] detaching gRPC server thread");
        serverThread.detach();
    } else if (executor != nullptr && bugatoneApi != nullptr) {
        buga_rpc_log("[RPCBugatoneProxy] creating gRPC thread");
        std::thread serverThread([executor=std::move(executor)] {
            buga_rpc_log("[RPCBugatoneProxy] gRPC thread started");  // , calling create_executor");
            // std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
            buga_rpc_log("[RPCBugatoneProxy] calling listen");
            createBugaGRPCServer()->listen(*executor, get_requested_port(), true);
            buga_rpc_log("[RPCBugatoneProxy] gRPC server listen done, thread returning");
        });
        buga_rpc_log("[RPCBugatoneProxy] detaching gRPC server thread");
        serverThread.detach();
    }

    return bugatoneApi;
}
