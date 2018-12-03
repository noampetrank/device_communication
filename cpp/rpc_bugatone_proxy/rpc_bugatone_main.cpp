#include <dlfcn.h>
#include <cstdio>

#ifdef __ANDROID__
#include <android/dlext.h>
#include <android/log.h>

#ifdef RPC_BUGATONE_MAIN_EXECUTABLE
#define myputs(msg) std::puts(msg)
#else
#define myputs(msg) __android_log_print(ANDROID_LOG_INFO, "Bugatone", "%s", msg)
#endif

const char* protolib_path = "libproto.so";
const char* rpc_server_path = "librpc_server.so";
const char* rpc_bugatone_proxy_path = "librpc_bugatone_proxy.so";

#else
#define myputs(msg) std::puts(msg)
#define android_dlopen_ext(path, method, extinfo) dlopen(path, method)

const char* protolib_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/libproto.so";
const char* rpc_server_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_server.so";
const char* rpc_bugatone_proxy_path = "/home/buga/device_communication/cpp/lib/linux_x86/Release/librpc_bugatone_proxy.so";

#endif

extern "C" void* _Z17createBugatoneApiv() {
//int main() {
    myputs("[RPCBugatoneMain] main createBugatoneApi called");

#ifdef __ANDROID__
    android_dlextinfo extinfo;
    extinfo.flags = ANDROID_DLEXT_FORCE_LOAD;
#endif

    void *protolib = android_dlopen_ext(protolib_path, RTLD_NOW, &extinfo);
    if (protolib == nullptr) {
        myputs("[RPCBugatoneMain] Failed to load protolib");
        myputs(dlerror());
        return nullptr;
    }

    void *rpc_server = android_dlopen_ext(rpc_server_path, RTLD_NOW, &extinfo);
    if (rpc_server == nullptr) {
        myputs("[RPCBugatoneMain] Failed to load rpc_server");
        myputs(dlerror());
        return nullptr;
    }

    void *rpc_bugatone_proxy = dlopen(rpc_bugatone_proxy_path, RTLD_NOW);
    if (rpc_bugatone_proxy == nullptr) {
        myputs("[RPCBugatoneMain] Failed to load rpc_bugatone_proxy");
        return nullptr;
    }

    auto createBugatoneApi = (void *(*)()) dlsym(rpc_bugatone_proxy, "_Z17createBugatoneApiv");
    if (createBugatoneApi == nullptr) {
        myputs("[RPCBugatoneMain] Failed to load createBugatoneApi");
        return nullptr;
    }

    myputs("[RPCBugatoneMain] calling createBugatoneApi");
    return createBugatoneApi();
}

int main() {
    _Z17createBugatoneApiv();
    myputs("[RPCBugatoneMain] enter any key to exit");
    std::getchar();
    return 0;
}