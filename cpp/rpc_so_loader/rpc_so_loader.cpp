#include "rpc_so_loader.h"
#include "rpc_bindings/bugarpc.h"
#include "rpc_bindings/rpc_log.h"
#include <vector>
#include <map>
#include <thread>
#include <algorithm>
#include <dlfcn.h>
#include <dirent.h>
#include <sys/stat.h>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <condition_variable>


std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();


class SoLoaderExecutor : public IRemoteProcedureExecutor {
public:
    explicit SoLoaderExecutor(const std::string &sosDir);
    Buffer executeProcedure(const std::string &procedureName, const Buffer &params) override;
    std::string getVersion() override { return "1.0"; }

private:
    struct RpcData {
        std::unique_ptr<IRemoteProcedureServer> server = nullptr;
        std::thread thrd;
        void *libHandle = nullptr;
        ~RpcData() {
            if (thrd.joinable()) {
                thrd.detach(); //TODO stop server and join instead of detach
            }
        }
    };
    std::map<int, RpcData> openRpcs;
    std::string sosDir;

    std::string getSoPath(int rpcId);
    void stopExecutor(RpcData& openRpc);
};

std::string SoLoaderExecutor::getSoPath(int rpcId) {
    return sosDir + std::to_string(rpcId) + ".so";
}

static void save_to_file(const std::string &path, const Buffer &what) {
    std::ofstream out(path.c_str(), std::ios_base::out | std::ios_base::binary);
    for (auto i : what)
        out << i;
}

SoLoaderExecutor::SoLoaderExecutor(const std::string &sosDir) : sosDir(sosDir) {
    mkdir(sosDir.c_str(), S_IRWXU | S_IRGRP |  S_IXGRP | S_IROTH | S_IXOTH);
    if (this->sosDir.back() != '/') {
        this->sosDir += '/';
    }
    buga_rpc_log("Starting so loader...");
}

void SoLoaderExecutor::stopExecutor(RpcData& openRpc) {
    if (openRpc.server) {
        openRpc.server->stop();

        if (openRpc.thrd.joinable()) {
            openRpc.thrd.join();
        }

        buga_rpc_log("After join");

        if (openRpc.libHandle != nullptr) {
            dlclose(openRpc.libHandle);
            openRpc.libHandle = nullptr;
        }
    }
}

Buffer SoLoaderExecutor::executeProcedure(const std::string &procedureName, const Buffer &params) {
    if (procedureName == "install_so") {  // params="rpcId,so_binary"
        auto commaIt = std::find(params.begin(), params.end(), ',');
        if (commaIt != params.end()) {
            std::string sRpcId(params.begin(), commaIt);
            buga_rpc_log("Requested to install so for rpcId " + sRpcId);
            int rpcId = std::stoi(sRpcId);

            // If there is a running RPC with this rpcId, close it.
            auto openRpcIt = openRpcs.find(rpcId);
            if (openRpcIt != openRpcs.end()) {
                auto& openRpc = openRpcIt->second;
                stopExecutor(openRpc);
            }

            Buffer soBinary(commaIt + 1, params.end());
            save_to_file(getSoPath(rpcId), soBinary);
            buga_rpc_log("Installed so for rpcId " + sRpcId);
        } else {
            buga_rpc_log("install_so called with wrong params");
            return "FAIL";
        }
        return "OK";
    } else if (procedureName == "run_so") {  // params="rpcId"
        std::string sRpcId(params.begin(), params.end());
        buga_rpc_log("Requested to run so for rpcId " + sRpcId);
        int rpcId = std::stoi(sRpcId);
        auto& openRpc = openRpcs[rpcId];

        stopExecutor(openRpc);

        void *lib = openRpc.libHandle = dlopen(getSoPath(rpcId).c_str(), RTLD_LAZY);
        if (lib != nullptr && dlerror() == NULL) {
            auto create_executor = (CreateExecutorFunc) dlsym(lib, "create_executor");

            buga_rpc_log("Loaded " + sRpcId + ".so");
            if (create_executor != nullptr && dlerror() == NULL) {
                std::mutex m;
                std::condition_variable cv;
                bool flag = false;

                openRpc.server = createBugaGRPCServer();
                openRpc.thrd = std::thread([create_executor, rpcId, &m, &cv, &flag, server=openRpc.server.get()] {
                    buga_rpc_log("Creating executor for rpcId " + std::to_string(rpcId));
                    std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
                    buga_rpc_log("Starting server for rpcId " + std::to_string(rpcId));
                    server->listen(*executor, rpcId, false);

                    {
                        std::lock_guard<std::mutex> lock(m);
                        flag = true;
                    }

                    cv.notify_one();
                    server->wait();

                    buga_rpc_log("Server stopped for rpcId " + std::to_string(rpcId));
                });

                std::unique_lock<std::mutex> lock(m);
                cv.wait(lock, [&] { return flag; });
            } else {
                buga_rpc_log("Could not load func for rpcId " + sRpcId + " (" + dlerror() + ")");
                return "FAIL";
            }
        } else {
            buga_rpc_log("Couldn't load so for rpcId " + sRpcId + " (" + dlerror() + ")");
            return "FAIL";
        }

        return "OK";
    } else if (procedureName == "stop_so") {
        std::string sRpcId(params.begin(), params.end());
        buga_rpc_log("Requested to stop so for rpcId " + sRpcId);
        int rpcId = std::stoi(sRpcId);

        auto openRpc_it = openRpcs.find(rpcId);
        if (openRpc_it != std::end(openRpcs)) {
            stopExecutor(openRpc_it->second);
            return "OK";
        } else {
            return "NOT_RUNNING";
        }
    }
    return "NOT_SUPPORTED";
}

void init(const char *sosDir) {
    SoLoaderExecutor executor(sosDir);
    createBugaGRPCServer()->listen(executor, 29998, true);
}

#ifdef SO_LOADER_EXECUTABLE
int main() {
    init("/home/buga/device_communication/cpp/bin/linux_x86/Release/sos/");
    return 0;
}
#endif
