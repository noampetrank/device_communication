#include <jni.h>
#include <string>
#include <dlfcn.h>
#include <android/dlext.h>
#include <android/log.h>
#include <thread>

extern "C" JNIEXPORT jstring JNICALL
Java_com_buga_rpcsoloader_RpcSoLoaderActivity_startRpcSoLoader(
        JNIEnv *env,
        jobject, /* this */
        jstring jLibsPath) {
    jboolean isCopy;
    const char* libsPath = env->GetStringUTFChars(jLibsPath, &isCopy);
    std::string sLibsPath = libsPath;
    __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "Starting thread");

    static std::thread rpcLoaderThread = std::thread([sLibsPath] {
        android_dlextinfo extinfo;
        extinfo.flags = ANDROID_DLEXT_FORCE_LOAD;

        __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "Loading load_and_init at path %s", sLibsPath.c_str());
        std::string librpc_so_loader_main = sLibsPath + "/librpc_so_loader_main.so";
        void *lib = android_dlopen_ext(librpc_so_loader_main.c_str(), RTLD_NOW, &extinfo);
        __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "dlopened %s @%p", librpc_so_loader_main.c_str(), lib);

        auto load_and_init = (void (*)(const char* protolib_path, const char* rpc_server_path, const char* rpc_so_loader_path)) dlsym(lib, "_Z13load_and_initPKcS0_S0_");
        if (load_and_init == nullptr) {
            __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "%s: %s", "Failed to load load_and_init", dlerror());
            return;
        }

        __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "Calling load_and_init");
        std::string libproto_path = sLibsPath + "/libproto.so";
        std::string librpc_server_path = sLibsPath + "/librpc_server.so";
        std::string librpc_so_loader_path = sLibsPath + "/librpc_so_loader.so";
        load_and_init(libproto_path.c_str(), librpc_server_path.c_str(), librpc_so_loader_path.c_str());
    });

    if (isCopy == JNI_TRUE) {
        env->ReleaseStringUTFChars(jLibsPath, libsPath);
    }

    std::string hello = "Hello from C++";
    return env->NewStringUTF(hello.c_str());
}
