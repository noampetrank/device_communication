#include "rpc_so_loader.h"
#include "rpc_bindings/bugarpc.h"
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
};

/*
static std::vector<int> existing_rpc_ids() {
    // https://stackoverflow.com/questions/612097/how-can-i-get-the-list-of-files-in-a-directory-using-c-or-c
    std::vector<int> rpcIds;

    auto dirp = opendir(PATH_TO_SOS.c_str());
    dirent *dp;
    while ((dp = readdir(dirp)) != NULL) {
        size_t namlen = strlen(dp->d_name);
        if (namlen > 3 && !strcmp(dp->d_name + namlen - 3, ".so")) {
            rpcIds.push_back(std::stoi(std::string(dp->d_name, namlen - 3)));
        }
    }
    closedir(dirp);
    return rpcIds;
}
*/

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
    std::cout << "Starting so loader..." << std::endl;
}

Buffer SoLoaderExecutor::executeProcedure(const std::string &procedureName, const Buffer &params) {
    if (procedureName == "install_so") {  // params="rpcId,so_binary"
        auto commaIt = std::find(params.begin(), params.end(), ',');
        if (commaIt != params.end()) {
            std::string sRpcId(params.begin(), commaIt);
            std::cout << "Requested to install so for rpcId " + sRpcId << std::endl;
            int rpcId = std::stoi(sRpcId);

            // If there is a running RPC with this rpcId, close it.
            auto openRpcIt = openRpcs.find(rpcId);
            if (openRpcIt != openRpcs.end()) {
                auto& openRpc = openRpcIt->second;
                if (openRpc.thrd.joinable()) {
                    openRpc.thrd.join();  //TODO stop the server?
                }

                if (openRpc.libHandle != nullptr) {
                    dlclose(openRpc.libHandle);
                    openRpc.libHandle = nullptr;
                }
            }

            Buffer soBinary(commaIt + 1, params.end());
            save_to_file(getSoPath(rpcId), soBinary);
            std::cout << "Installed so for rpcId " + sRpcId << std::endl;
        } else {
            std::cout << "install_so called with wrong params" << std::endl;
            return "FAIL";
        }
        return "OK";
    } else if (procedureName == "run_so") {  // params="rpcId"
        std::string sRpcId(params.begin(), params.end());
        std::cout << "Requested to run so for rpcId " + sRpcId << std::endl;
        int rpcId = std::stoi(sRpcId);
        auto& openRpc = openRpcs[rpcId];

        void *lib = openRpc.libHandle = dlopen(getSoPath(rpcId).c_str(), RTLD_LAZY);
        if (lib != nullptr && dlerror() == NULL) {
            auto create_executor = (CreateExecutorFunc) dlsym(lib, "create_executor");
            std::cout << "Loaded so " + sRpcId + ".so from handle " << lib << " and function pointer "
                      << (void*)create_executor << std::endl;
            if (create_executor != nullptr && dlerror() == NULL) {
                std::mutex m;
                std::condition_variable cv;
                bool flag = false;

                openRpc.thrd = std::thread([create_executor, rpcId, &m, &cv, &flag] {
                    std::cout << "Creating executor for rpcId " + std::to_string(rpcId) << std::endl;
                    std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
                    std::cout << "Starting server for rpcId " + std::to_string(rpcId) << std::endl;
                    auto server = createBugaGRPCServer();
                    server->listen(*executor, rpcId, false);

                    {
                        std::lock_guard<std::mutex> lock(m);
                        flag = true;
                    }

                    cv.notify_one();
                    server->wait();

                    std::cout << "Server stopped for rpcId " + std::to_string(rpcId) << std::endl;
                });

                std::unique_lock<std::mutex> lock(m);
                cv.wait(lock, [&] { return flag; });
            } else {
                std::cout << "Could not load func for rpcId " + sRpcId << " (" << dlerror() << ")" << std::endl;
                return "FAIL";
            }
        } else {
            std::cout << "Could not load so for rpcId " + sRpcId << " (" << dlerror() << ")" << std::endl;
            return "FAIL";
        }

        return "OK";
    }
    return "NOT_SUPPORTED";
}

void init(const char *sosDir) {
    SoLoaderExecutor executor(sosDir);
    createBugaGRPCServer()->listen(executor, 29998, true);
}

#ifdef SO_LOADER_EXECUTABLE
int main() {
    init("sos/");
    return 0;
}
#endif
