#include "rpc_so_loader.h"
#include "rpc_bindings/bugarpc.h"
#include <vector>
#include <thread>
#include <algorithm>
#include <dlfcn.h>
#include <dirent.h>
#include <sys/stat.h>
#include <cstring>
#include <fstream>
#include <iostream>


static const std::string PATH_TO_SOS = "sos/";


class SoLoaderExecutor : public IRemoteProcedureExecutor {
public:
    SoLoaderExecutor();
    Buffer executeProcedure(const std::string &procedureName, const Buffer &params) override;
    std::string getVersion() override { return "1.0"; }

private:
    std::vector<std::thread> openLibs;
    std::vector<int> rpcIds;
};


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

static std::string get_so_path(int rpcId) {
    return PATH_TO_SOS + std::to_string(rpcId) + ".so";
}

static void save_to_file(const std::string &path, const Buffer &what) {
    std::ofstream out(path.c_str(), std::ios_base::out | std::ios_base::binary);
    for (auto i : what)
        out << i;
}

SoLoaderExecutor::SoLoaderExecutor() {
    mkdir(PATH_TO_SOS.c_str(), S_IRWXU | S_IRGRP |  S_IXGRP | S_IROTH | S_IXOTH);
    rpcIds = existing_rpc_ids();
    std::cout << "Starting so loader..." << std::endl;
}

Buffer SoLoaderExecutor::executeProcedure(const std::string &procedureName, const Buffer &params) {
    if (procedureName == "install_so") {  // params="rpcId,so_binary"
        auto commaIt = std::find(params.begin(), params.end(), ',');
        if (commaIt != params.end()) {
            std::string sRpcId(params.begin(), commaIt);
            std::cout << "Requested to install so for rpcId " + sRpcId << std::endl;
            int rpcId = std::stoi(sRpcId);
            Buffer soBinary(commaIt + 1, params.end());
            save_to_file(get_so_path(rpcId), soBinary);
            if (std::find(rpcIds.begin(), rpcIds.end(), rpcId) != rpcIds.end()) {
                rpcIds.push_back(rpcId);
                std::cout << "Installed so for rpcId " + sRpcId << std::endl;
            } else {
                std::cout << "rpcId " + sRpcId + " already installed" << std::endl;
            }
        }
        return "OK";
    } else if (procedureName == "run_so") {  // params="rpcId"
        std::string sRpcId(params.begin(), params.end());
        std::cout << "Requested to run so for rpcId " + sRpcId << std::endl;
        int rpcId = std::stoi(sRpcId);
        if (std::find(rpcIds.begin(), rpcIds.end(), rpcId) != rpcIds.end()) {
            void* lib = dlopen(get_so_path(rpcId).c_str(), RTLD_LAZY);
            typedef std::unique_ptr<IRemoteProcedureExecutor> (*CreateExecutorFunc)();
            auto create_executor = (CreateExecutorFunc)dlsym(lib, "create_executor");
            std::cout << "Loaded so " + sRpcId + ".so from handle " << lib << " and function pointer " << create_executor << std::endl;
            if (create_executor != nullptr) {
                openLibs.emplace_back([create_executor, rpcId] {
                    std::cout << "Creating executor for rpcId " + std::to_string(rpcId) << std::endl;
                    std::unique_ptr<IRemoteProcedureExecutor> executor = create_executor();
                    std::cout << "Starting server for rpcId " + std::to_string(rpcId) << std::endl;
                    createBugaGRPCServer()->listen(*executor, rpcId, true);
                    std::cout << "Server stopped for rpcId " + std::to_string(rpcId) << std::endl;
                });
            }
        }
        return "OK";
    }
    return "NOT_SUPPORTED";
}

extern "C" {

void init() {
    SoLoaderExecutor executor;
    createBugaGRPCServer()->listen(executor, 29998, true);
}

}

#ifdef SO_LOADER_EXECUTABLE
int main() {
    init();
    return 0;
}
#endif
