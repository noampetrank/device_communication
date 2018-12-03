#include <dlfcn.h>
#include <cstdio>
#include "utils/rpc_log.h"

#ifdef __ANDROID__
#include <android/dlext.h>

const char* protolib_path = "libproto.so";
const char* rpc_server_path = "librpc_server.so";
const char* rpc_bugatone_proxy_path = "librpc_bugatone_proxy.so";

#else
#define android_dlopen_ext(path, method, extinfo) dlopen(path, method)

const char* protolib_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/libproto.so";
const char* rpc_server_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_server.so";
const char* rpc_bugatone_proxy_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_bugatone_proxy.so";

#endif

extern "C" void* _Z17createBugatoneApiv() {
//int main() {
    buga_rpc_log("[RPCBugatoneMain] main createBugatoneApi called");

#ifdef __ANDROID__
    android_dlextinfo extinfo;
    extinfo.flags = ANDROID_DLEXT_FORCE_LOAD;
#endif

    void *protolib = android_dlopen_ext(protolib_path, RTLD_NOW, &extinfo);
    if (protolib == nullptr) {
        buga_rpc_log("[RPCBugatoneMain] Failed to load protolib");
        buga_rpc_log(dlerror());
        return nullptr;
    }

    void *rpc_server = android_dlopen_ext(rpc_server_path, RTLD_NOW, &extinfo);
    if (rpc_server == nullptr) {
        buga_rpc_log("[RPCBugatoneMain] Failed to load rpc_server");
        buga_rpc_log(dlerror());
        return nullptr;
    }

    void *rpc_bugatone_proxy = dlopen(rpc_bugatone_proxy_path, RTLD_NOW);
    if (rpc_bugatone_proxy == nullptr) {
        buga_rpc_log("[RPCBugatoneMain] Failed to load rpc_bugatone_proxy");
        return nullptr;
    }

    auto createBugatoneApi = (void *(*)()) dlsym(rpc_bugatone_proxy, "_Z17createBugatoneApiv");
    if (createBugatoneApi == nullptr) {
        buga_rpc_log("[RPCBugatoneMain] Failed to load createBugatoneApi");
        return nullptr;
    }

    buga_rpc_log("[RPCBugatoneMain] calling createBugatoneApi");
    return createBugatoneApi();
}


#ifdef RPC_BUGATONE_MAIN_EXECUTABLE
int main() {
    _Z17createBugatoneApiv();
    buga_rpc_log("[RPCBugatoneMain] enter any key to exit");
    std::getchar();
    return 0;
}
#endif
