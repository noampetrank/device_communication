#include <atomic>
#include <chrono>
#include <thread>

#include <jni.h>
#include <android/log.h>

#include "rpc_impl/buga_grpc_server.h"
#include "rpc_impl/buga_rpc_executor.h"


std::atomic<bool> stop_server(false);

void grpc_logcat_func(gpr_log_func_args *args) {
    const int n = 65536;
    const int limit = 1023;
    char full[65536];
    char chunk[limit+1];
    char *p = full;
    snprintf(full, n, "%s:%d: %s", args->file, args->line, args->message);

    android_LogPriority priority = ANDROID_LOG_VERBOSE;
    if (args->severity == GPR_LOG_SEVERITY_DEBUG)
        priority = ANDROID_LOG_DEBUG;
    else if (args->severity == GPR_LOG_SEVERITY_INFO)
        priority = ANDROID_LOG_INFO;
    else if (args->severity == GPR_LOG_SEVERITY_ERROR)
        priority = ANDROID_LOG_ERROR;

    while (true) {
        int ret = snprintf(chunk, limit+1, "%s", p);
        __android_log_print(priority, "BugaGrpcLogProxy", "%s", chunk);
        if (ret <= limit)
            return;
        p += limit;
    }
}

bool StartServer(JNIEnv* env, jobject obj, jmethodID is_cancelled_mid,
                 int port) {
    const int host_port_buf_size = 1024;
    char host_port[host_port_buf_size];
    snprintf(host_port, host_port_buf_size, "0.0.0.0:%d", port);

    gpr_set_log_function(grpc_logcat_func);
    GRemoteProcedureServer server(host_port);
    BugaRpcExecutor bugaRpcExecutor;
    try {
        server.listen(bugaRpcExecutor, true);
    } catch (const GRPCServerError &err) {
        return false;
    }

//    while (!stop_server.load()) {
//        // Check with the Java code to see if the user has requested the server stop or the app is no
//        // longer in the foreground.
//        jboolean is_cancelled = env->CallBooleanMethod(obj, is_cancelled_mid);
//        if (is_cancelled == JNI_TRUE) {
//            stop_server = true;
//        }
//        std::this_thread::sleep_for(std::chrono::milliseconds(100));
//    }

    //TODO: Listen on another thread, and poll is_cancelled on this one to shutdown the server when asked to.
    return true;
}

// Send an RPC and return the response. Invoked from Java code.
extern "C" JNIEXPORT jstring JNICALL
//Java_com_bugatone_grpc_cpp_BugaGrpcActivity_sayHello(
Java_com_buga_grpc_bugagrpcecho_BugaGrpcActivity_sayHello(
        JNIEnv* env, jobject obj_unused, jstring host_raw, jint port_raw,
        jstring message_raw)
{
    return env->NewStringUTF("Not implemented");
}

// Start the server. Invoked from Java code.
extern "C" JNIEXPORT bool JNICALL
//Java_com_bugatone_grpc_cpp_BugaGrpcActivity_startServer(
Java_com_buga_grpc_bugagrpcecho_BugaGrpcActivity_startServer(
        JNIEnv* env, jobject obj_this, jint port_raw)
{
    int port = static_cast<int>(port_raw);

    jclass cls = env->GetObjectClass(obj_this);
    jmethodID is_cancelled_mid =
            env->GetMethodID(cls, "isRunServerTaskCancelled", "()Z");

    stop_server = false;

    return StartServer(env, obj_this, is_cancelled_mid, port);
}


// Stp the server. Invoked from Java code.
extern "C" JNIEXPORT bool JNICALL
//Java_com_bugatone_grpc_cpp_BugaGrpcActivity_startServer(
Java_com_buga_grpc_bugagrpcecho_BugaGrpcActivity_stopServer(
        JNIEnv* env, jobject obj_this, jint port_raw)
{
    int port = static_cast<int>(port_raw);

    jclass cls = env->GetObjectClass(obj_this);
    jmethodID is_cancelled_mid =
            env->GetMethodID(cls, "isRunServerTaskCancelled", "()Z");

    stop_server = false;

    return StartServer(env, obj_this, is_cancelled_mid, port);
}
