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
        if (lib == nullptr) {
            __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "%s: %s", "Failed to dlopen librpc_so_loader_main: %s", dlerror());
            return;
        }

        auto load_and_init = (void (*)(const char* sosDir)) dlsym(lib, "_Z13load_and_initPKc");
        if (load_and_init == nullptr) {
            __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "%s: %s", "Failed to dlsym load_and_init", dlerror());
            return;
        }

        __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "Calling load_and_init");
        load_and_init(sLibsPath.c_str());
    });

    if (isCopy == JNI_TRUE) {
        env->ReleaseStringUTFChars(jLibsPath, libsPath);
    }

    std::string hello = "Hello from C++";
    return env->NewStringUTF(hello.c_str());
}
