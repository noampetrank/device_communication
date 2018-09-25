#include <atomic>
#include <chrono>
#include <thread>
#include <vector>

#include <jni.h>
#include <android/log.h>

#include "rpc_impl/buga_grpc_server.h"
#include "rpc_bindings/remote_procedure_execution.h"


#define JNI_VERSION JNI_VERSION_1_6


// This function splits long gRPC log prints into messages that logcat can handle.
void grpc_logcat_func(gpr_log_func_args *args) {
    const int n = 65536;
    const int limit = 1023;
    char full[n];
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

static struct {
    JavaVM *jvm = NULL;
    jweak executorObj = NULL;
    jmethodID executeProcedure = NULL;
    jclass clsMarshaler = NULL;
    jmethodID marshalerCtor = NULL;
    jfieldID marshalerContent = NULL;
} context;

static JNIEnv *get_env(JavaVM *jvm, int &get_env_stat) {
    JNIEnv *g_env;
    if (NULL == jvm) {
        __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "No VM");
        return NULL;
    }

    //  double check it's all ok
    JavaVMAttachArgs args;
    args.version = JNI_VERSION;
    args.name = NULL;
    args.group = NULL;

    get_env_stat = jvm->GetEnv((void **) &g_env, args.version);

    if (get_env_stat == JNI_EDETACHED) {
        __android_log_print(ANDROID_LOG_WARN, "BugaGrpcLog", "Not attached");
        if (jvm->AttachCurrentThread(&g_env, &args) != 0) {
            __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "Failed to attach");
        }
    } else if (get_env_stat == JNI_OK) {
        __android_log_print(ANDROID_LOG_VERBOSE, "BugaGrpcLog", "JNI_OK");
    } else if (get_env_stat == JNI_EVERSION) {
        __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "Version not supported");
    }

    return g_env;
}

static void release_env(JNIEnv *env, JavaVM *jvm, int &get_env_stat) {
    if (env->ExceptionCheck()) {
        __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "JNI code encountered an exception");
        env->ExceptionDescribe();
    }

    if (get_env_stat == JNI_EDETACHED) {
        jvm->DetachCurrentThread();
    }
}

static jobject marshaledToJava(JNIEnv *env, const MarshaledObject &mo) {
    jobject jo = env->NewObject(context.clsMarshaler, context.marshalerCtor);
    jstring content = env->NewStringUTF(mo->c_str());
    env->SetObjectField(jo, context.marshalerContent, content);
    env->DeleteLocalRef(content);
    return jo;
}

static MarshaledObject marshaledFromJava(JNIEnv *env, const jobject &jo) {
    jstring content_field = reinterpret_cast<jstring>(env->GetObjectField(jo, context.marshalerContent));
    const char *content = env->GetStringUTFChars(content_field, NULL);
    MarshaledObject mo = std::make_shared<std::string>(content);
    env->ReleaseStringUTFChars(content_field, content);
    return mo;
}

static class : public StandardRemoteProcedureExecutor {
protected:

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshaledObject executeProcedure(std::string procedureName, const MarshaledObject &params) override {
        MarshaledObject ret;
        int get_env_stat;
        JNIEnv *env = get_env(context.jvm, get_env_stat);

        if (env != NULL) {
            jstring jproc_name = env->NewStringUTF(procedureName.c_str());
            jobject jparams = marshaledToJava(env, params);
            jobject jret = env->CallObjectMethod(context.executorObj, context.executeProcedure, jproc_name, jparams);
            if (!env->ExceptionCheck())
                ret = marshaledFromJava(env, jret);
            env->DeleteLocalRef(jproc_name);
        }

        release_env(env, context.jvm, get_env_stat);
        return ret;
    }

} bugaRpcExecutor;




jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    context.jvm = vm; // Store jvm reference for later call

    // Obtain the JNIEnv from the VM and confirm JNI_VERSION
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION) != JNI_OK)
        return JNI_ERR;

    jclass tmpClsMarshaler = env->FindClass("com/buga/grpc/cpp/MarshaledObject");
    context.clsMarshaler = (jclass) env->NewGlobalRef(tmpClsMarshaler);
    env->DeleteLocalRef(tmpClsMarshaler);
    context.marshalerCtor = env->GetMethodID(context.clsMarshaler, "<init>", "()V");
    context.marshalerContent = env->GetFieldID(context.clsMarshaler, "content", "Ljava/lang/String;");

    // Return the JNI Version as required by method
    return JNI_VERSION;
}


void JNI_OnUnload(JavaVM *vm, void *reserved) {

    // Obtain the JNIEnv from the VM
    // NOTE: some re-do the JNI Version check here, but I find that redundant
    JNIEnv* env;
    vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION);

    // Destroy the global references
    env->DeleteGlobalRef(context.clsMarshaler);
    if (context.executorObj != NULL)
        env->DeleteWeakGlobalRef(context.executorObj);
}


// Register RPC executor to receive calls from the client. Invoked from Java code.
extern "C" JNIEXPORT void JNICALL
Java_com_buga_grpc_cpp_BugaGrpc_registerExecutor(
        JNIEnv *env, jobject instance, jobject listener)
{
    context.executorObj = env->NewWeakGlobalRef(listener);
    jclass clsExecutor = env->GetObjectClass(context.executorObj);
    context.executeProcedure = env->GetMethodID(clsExecutor, "executeProcedure", "(Ljava/lang/String;Lcom/buga/grpc/cpp/MarshaledObject;)Lcom/buga/grpc/cpp/MarshaledObject;");
    env->DeleteLocalRef(clsExecutor);
}


static std::unique_ptr<std::thread> server_thread;
static std::unique_ptr<GRemoteProcedureServer> server;

void server_wait() {
    __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Buga gRPC server starts waiting for messages");
    int get_env_stat;
    JNIEnv *env = get_env(context.jvm, get_env_stat);

    server->wait();

    release_env(env, context.jvm, get_env_stat);
    __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Buga gRPC server stops waiting for messages");
}


// Start the gRPC server
extern "C" JNIEXPORT jboolean JNICALL
Java_com_buga_grpc_cpp_BugaGrpc_startServer(
        JNIEnv *env, jobject instance, jint jport)
{
    __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Starting Buga gRPC server");
    if (server_thread.get()) {
        __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "Buga gRPC server was already started!");
        return JNI_FALSE;
    }

    int port = static_cast<int>(jport);
    const int host_port_buf_size = 1024;
    char host_port[host_port_buf_size];
    snprintf(host_port, host_port_buf_size, "0.0.0.0:%d", port);

    gpr_set_log_function(grpc_logcat_func);
    server = std::make_unique<GRemoteProcedureServer>(host_port);
    try {
        server->listen(bugaRpcExecutor, false);
    } catch (const GRPCServerError &err) {
        __android_log_print(ANDROID_LOG_ERROR, "BugaGrpcLog", "Couln't start Buga gRPC server!");
        return JNI_FALSE;
    }

    server_thread = std::make_unique<std::thread>(server_wait);
    __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Started Buga gRPC server");
    return JNI_TRUE;
}


// Stop the gRPC server
extern "C" JNIEXPORT void JNICALL
Java_com_buga_grpc_cpp_BugaGrpc_stopServer(
        JNIEnv *env, jobject instance)
{
    __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Stopping Buga gRPC server");
    if (server.get()) {
        server->stop();
        server_thread->join();
        server_thread = NULL;
        __android_log_print(ANDROID_LOG_INFO, "BugaGrpcLog", "Stopped Buga gRPC server");
    }
}
