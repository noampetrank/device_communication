#ifndef GRPC_TEST_RPC_LOG_H
#define GRPC_TEST_RPC_LOG_H

#include <string>

#if defined(__ANDROID__) and not defined(RPC_LOADER_EXECUTABLE) and not defined(RPC_SO_LOADER_MAIN_EXECUTABLE) and not defined(RPC_BUGATONE_MAIN_EXECUTABLE)
#include <android/log.h>
inline void buga_rpc_log(const std::string &msg) {
    __android_log_print(ANDROID_LOG_INFO, "RpcBugatone", "%s", msg.c_str());
}
#else
inline void buga_rpc_log(const std::string &msg) {
    std::puts(msg.c_str());
}
#endif

#endif //GRPC_TEST_RPC_LOG_H
