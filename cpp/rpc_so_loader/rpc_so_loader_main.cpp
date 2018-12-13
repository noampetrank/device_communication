#include <dlfcn.h>
#include <cstdio>
#include "utils/rpc_log.h"

#ifdef __ANDROID__
#include <android/dlext.h>

#ifdef RPC_SO_LOADER_MAIN_EXECUTABLE

const char* protolib_path = "/data/local/tmp/rpc/libproto.so";
const char* rpc_server_path = "/data/local/tmp/rpc/librpc_server.so";
const char* rpc_so_loader_path = "/data/local/tmp/rpc/librpc_so_loader.so";

#else

// These will be the addreses when loaded in Java.
// Need to set them correctly later.
const char* protolib_path = "libproto.so";
const char* rpc_server_path = "librpc_server.so";
const char* rpc_so_loader_path = "librpc_so_loader.so";

#endif

#else

#define android_dlopen_ext(path, method, extinfo) dlopen(path, method)

#endif

void load_and_init(const char* sosDir) {
    const int MAX_PATH = 4096;
    char protolib_path[MAX_PATH], rpc_server_path[MAX_PATH], rpc_so_loader_path[MAX_PATH];
    snprintf(protolib_path, MAX_PATH, "%s/libproto.so", sosDir);
    snprintf(rpc_server_path, MAX_PATH, "%s/librpc_server.so", sosDir);
    snprintf(rpc_so_loader_path, MAX_PATH, "%s/librpc_so_loader.so", sosDir);

    buga_rpc_log("[RPCSoLoaderMain] load_and_init called");

#ifdef __ANDROID__
    android_dlextinfo extinfo;
    extinfo.flags = ANDROID_DLEXT_FORCE_LOAD;
#endif

    void *protolib = android_dlopen_ext(protolib_path, RTLD_NOW, &extinfo);
    if (protolib == nullptr) {
        buga_rpc_log("[RPCSoLoaderMain] Failed to load protolib");
        buga_rpc_log(dlerror());
        return;
    }

    void *rpc_server = android_dlopen_ext(rpc_server_path, RTLD_NOW, &extinfo);
    if (rpc_server == nullptr) {
        buga_rpc_log("[RPCSoLoaderMain] Failed to load rpc_server");
        buga_rpc_log(dlerror());
        return;
    }

    void *rpc_so_loader = android_dlopen_ext(rpc_so_loader_path, RTLD_NOW, &extinfo);
    if (rpc_so_loader == nullptr) {
        buga_rpc_log("[RPCSoLoaderMain] Failed to load rpc_so_loader");
        buga_rpc_log(rpc_so_loader_path);
        buga_rpc_log(dlerror());
        return;
    }

    auto init = (void (*)(const char *sosDir)) dlsym(rpc_so_loader, "_Z4initPKc");
    if (init == nullptr) {
        buga_rpc_log("[RPCSoLoaderMain] Failed to load init");
        buga_rpc_log(dlerror());
        return;
    }

    buga_rpc_log("[RPCSoLoaderMain] calling init");
    init(sosDir);
}

#ifdef RPC_SO_LOADER_MAIN_EXECUTABLE
int main() {
    const char *sosDir = "/home/buga/device_communication/cpp/lib/linux_x86/Release";

    load_and_init(sosDir);
    buga_rpc_log("[RPCSoLoaderMain] enter any key to exit");
    std::getchar();
    return 0;
}
#endif
