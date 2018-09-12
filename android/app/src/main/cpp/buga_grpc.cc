#include <atomic>
#include <chrono>
#include <thread>

#include <jni.h>

#include "rpc_impl/buga_grpc_server.h"
#include "rpc_impl/buga_rpc_executor.h"


std::atomic<bool> stop_server(false);

void StartServer(JNIEnv* env, jobject obj, jmethodID is_cancelled_mid,
                 int port) {
  const int host_port_buf_size = 1024;
  char host_port[host_port_buf_size];
  snprintf(host_port, host_port_buf_size, "0.0.0.0:%d", port);

  GRemoteProcedureServer server(host_port);
  BugaRpcExecutor bugaRpcExecutor;
  server.listen(bugaRpcExecutor, false);

  while (!stop_server.load()) {
    // Check with the Java code to see if the user has requested the server stop or the app is no
    // longer in the foreground.
    jboolean is_cancelled = env->CallBooleanMethod(obj, is_cancelled_mid);
    if (is_cancelled == JNI_TRUE) {
      stop_server = true;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
}

// Send an RPC and return the response. Invoked from Java code.
extern "C" JNIEXPORT jstring JNICALL
Java_com_bugatone_grpc_cpp_HelloworldActivity_sayHello(
    JNIEnv* env, jobject obj_unused, jstring host_raw, jint port_raw,
    jstring message_raw)
{
  return env->NewStringUTF("Not implemented");
}

// Start the server. Invoked from Java code.
extern "C" JNIEXPORT void JNICALL
Java_com_bugatone_grpc_cpp_HelloworldActivity_startServer(
    JNIEnv* env, jobject obj_this, jint port_raw)
{
  int port = static_cast<int>(port_raw);

  jclass cls = env->GetObjectClass(obj_this);
  jmethodID is_cancelled_mid =
      env->GetMethodID(cls, "isRunServerTaskCancelled", "()Z");

  stop_server = false;

  StartServer(env, obj_this, is_cancelled_mid, port);
}
