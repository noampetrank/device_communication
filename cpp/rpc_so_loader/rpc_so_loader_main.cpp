#include <dlfcn.h>
#include <cstdio>

#ifdef __ANDROID__
#include <android/dlext.h>
#include <android/log.h>

#ifdef RPC_SO_LOADER_MAIN_EXECUTABLE
#define myputs(msg) std::puts(msg)

const char* protolib_path = "/data/local/tmp/rpc/libproto.so";
const char* rpc_server_path = "/data/local/tmp/rpc/librpc_server.so";
const char* rpc_so_loader_path = "/data/local/tmp/rpc/librpc_so_loader.so";

#else
#define myputs(msg) __android_log_print(ANDROID_LOG_INFO, "Bugatone", "%s", msg)

// These will be the addreses when loaded in Java.
// Need to set them correctly later.
const char* protolib_path = "libproto.so";
const char* rpc_server_path = "librpc_server.so";
const char* rpc_so_loader_path = "librpc_so_loader.so";

#endif

#else
#define myputs(msg) std::puts(msg)
#define android_dlopen_ext(path, method, extinfo) dlopen(path, method)

#endif

void load_and_init(const char* protolib_path, const char* rpc_server_path, const char* rpc_so_loader_path) {
//int main() {
    myputs("[RPCSoLoaderMain] load_and_init called");

#ifdef __ANDROID__
    android_dlextinfo extinfo;
    extinfo.flags = ANDROID_DLEXT_FORCE_LOAD;
#endif

    void *protolib = android_dlopen_ext(protolib_path, RTLD_NOW, &extinfo);
    if (protolib == nullptr) {
        myputs("[RPCSoLoaderMain] Failed to load protolib");
        myputs(dlerror());
        return;
    }

    void *rpc_server = android_dlopen_ext(rpc_server_path, RTLD_NOW, &extinfo);
    if (rpc_server == nullptr) {
        myputs("[RPCSoLoaderMain] Failed to load rpc_server");
        myputs(dlerror());
        return;
    }

    void *rpc_so_loader = android_dlopen_ext(rpc_so_loader_path, RTLD_NOW, &extinfo);
    if (rpc_so_loader == nullptr) {
        myputs("[RPCSoLoaderMain] Failed to load rpc_so_loader");
        myputs(rpc_so_loader_path);
        myputs(dlerror());
        return;
    }

    auto init = (void (*)()) dlsym(rpc_so_loader, "_Z4initv");
    if (init == nullptr) {
        myputs("[RPCSoLoaderMain] Failed to load init");
        myputs(dlerror());
        return;
    }

    myputs("[RPCSoLoaderMain] calling init");
    init();
}

#ifdef RPC_SO_LOADER_MAIN_EXECUTABLE
int main() {
    const char* protolib_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/libproto.so";
    const char* rpc_server_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_server.so";
    const char* rpc_so_loader_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_so_loader.so";

    load_and_init(protolib_path, rpc_server_path, rpc_so_loader_path);
    myputs("[RPCSoLoaderMain] enter any key to exit");
    std::getchar();
    return 0;
}
#endif
