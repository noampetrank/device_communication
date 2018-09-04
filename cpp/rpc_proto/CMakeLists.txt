cmake_minimum_required(VERSION 3.2)

# GRPC and Protocol Buffers libraries location
list(APPEND CMAKE_PREFIX_PATH "/usr/local/lib")

# Cmake find modules
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../cmake")

find_package(Protobuf REQUIRED)
find_package(GRPC REQUIRED)

set(PROTOS
        ${CMAKE_CURRENT_SOURCE_DIR}/buga_rpc.proto
        )

set(PROTO_SRC_DIR ${CMAKE_CURRENT_BINARY_DIR}/proto-src)
file(MAKE_DIRECTORY ${PROTO_SRC_DIR})

protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${PROTO_SRC_DIR} ${PROTOS})
grpc_generate_cpp(GRPC_SRCS GRPC_HDRS ${PROTO_SRC_DIR} ${PROTOS})

# Building server
add_library(proto
        ${PROTO_SRCS}
        ${GRPC_SRCS}
        )

if (NOT MY_BUILD_ANDROID)
    set(THIS_LIB
            gRPC::grpc++_reflection
            protobuf::libprotobuf
            )
else ()
#    set(THIS_LIB
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc++_reflection.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc++.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc_unsecure.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc++_unsecure.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc_cronet.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgrpc++_cronet.so
##            /home/buga/Code/grpc-arm64/libs/opt/libgpr.so
##            /home/buga/Code/grpc-arm64/libs/opt/libaddress_sorting.so
##            /home/buga/Code/grpc-arm64/libs/opt/protobuf/libprotobuf.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/libgrpc++.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/libgrpc.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/libgpr.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/protobuf/libprotobuf.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/zlib/libz.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/cares/cares/lib/libcares.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/benchmark/test/liboutput_test_helper.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/benchmark/src/libbenchmark.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/boringssl/crypto/libcrypto.a
##            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/boringssl/libboringssl_gtest.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/boringssl/decrepit/libdecrepit.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/boringssl/ssl/libssl.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/protobuf/libprotobuf.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/zlib/libz.a
#            ${PROJECT_SOURCE_DIR}/dependencies/newtry/third_party/cares/cares/lib/libcares.a
#
#            log
#            )
    target_include_directories(proto PUBLIC ${GRPC_INCLUDE_DIR})
    set(CMAKE_INSTALL_RPATH ${PROJECT_SOURCE_DIR}/dependencies/grpc/lib/)

endif ()

target_include_directories(proto PUBLIC ${PROTO_SRC_DIR})
target_link_libraries(proto
        ${THIS_LIB}
        )
