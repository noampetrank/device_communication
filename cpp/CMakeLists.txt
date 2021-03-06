if (MY_BUILD_ANDROID)
    set(APP_STL c++_shared)
    set(CMAKE_ANDROID_STL_TYPE c++_shared)
    set(CMAKE_ANDROID_ARCH_ABI arm64-v8a)
    set(CMAKE_SYSTEM_NAME Android)
    set(CMAKE_ANDROID_STANDALONE_TOOLCHAIN $ENV{HOME}/android-toolchain)
    set(CMAKE_CXX_FLAGS "-O3")
    set(ARCH arm64)
    set(RUN_HAVE_POSIX_REGEX 0)
    set(RUN_HAVE_STD_REGEX 0)
    set(RUN_HAVE_STEADY_CLOCK 0)
else ()
    set(CMAKE_CXX_LINK_FLAGS "${CMAKE_CXX_LINK_FLAGS} -latomic")
    # Uncomment the following line to add debug symbols (also necessary for C++ debugging via Python)
    #    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -D_GLIBCXX_DEBUG")
    #    set(CMAKE_CXX_FLAGS "-fsanitize=thread -g")
    set(CMAKE_CXX_FLAGS "-g")
    #    set(CMAKE_CXX_FLAGS "-fsanitize=address -fno-omit-frame-pointer -g -O1")
    set(ARCH linux_x86)
endif ()

cmake_minimum_required(VERSION 3.10)
project(cpp)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(LIBRARY_OUTPUT_PATH ${CMAKE_CURRENT_SOURCE_DIR}/lib/${ARCH}/${CMAKE_BUILD_TYPE})
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_CURRENT_SOURCE_DIR}/bin/${ARCH}/${CMAKE_BUILD_TYPE})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/bin/${ARCH}/${CMAKE_BUILD_TYPE})

message(STATUS "Compiling for " ${ARCH})

add_subdirectory(rpc_proto)
message(STATUS "Proto source dir is at " ${PROTO_SRC_DIR})

# RPC server
add_library(rpc_server SHARED
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h
        rpc_impl/buga_grpc_server.cpp
        )
target_include_directories(rpc_server PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        build_linux_release/rpc_proto/proto-src
        )
target_link_libraries(rpc_server proto)


# Demo that runs RPC server+client on Linux
project(rpc_demo)
add_executable(rpc_demo
        demo_main.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h
        rpc_impl/buga_echo_executor.cpp
        rpc_impl/buga_echo_executor.h)
target_include_directories(rpc_demo PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
)
target_link_libraries(rpc_demo proto rpc_server)


# RPC loader executable
project(rpc_so_loader_exec)
add_executable(rpc_so_loader_exec
        rpc_so_loader/rpc_so_loader.h
        rpc_so_loader/rpc_so_loader.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h)
target_compile_definitions(rpc_so_loader_exec PRIVATE
        SO_LOADER_EXECUTABLE=1)
target_include_directories(rpc_so_loader_exec PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
)
target_link_libraries(rpc_so_loader_exec proto rpc_server)


# RPC loader shared library
project(rpc_so_loader)
add_library(rpc_so_loader SHARED
        rpc_so_loader/rpc_so_loader.h
        rpc_so_loader/rpc_so_loader.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h)
target_include_directories(rpc_so_loader PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        )
target_link_libraries(rpc_so_loader proto rpc_server)


# Daemon RPC main library
project(rpc_so_loader_main)
add_library(rpc_so_loader_main SHARED
        rpc_so_loader/rpc_so_loader_main.cpp)
target_include_directories(rpc_so_loader_main PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        )
if(MY_BUILD_ANDROID)
    target_link_libraries(rpc_so_loader_main android)
endif(MY_BUILD_ANDROID)


# Daemon RPC main executable - so not really daemon
project(rpc_so_loader_main_exec)
add_executable(rpc_so_loader_main_exec
        rpc_so_loader/rpc_so_loader_main.cpp)
target_include_directories(rpc_so_loader_main_exec PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        )
target_compile_definitions(rpc_so_loader_main_exec PRIVATE
        RPC_SO_LOADER_MAIN_EXECUTABLE=1
        )
if(MY_BUILD_ANDROID)
    target_link_libraries(rpc_so_loader_main_exec android)
else(MY_BUILD_ANDROID)
    target_link_libraries(rpc_so_loader_main_exec dl)
endif(MY_BUILD_ANDROID)


# Daemon RPC proxy library
project(rpc_bugatone_proxy)
add_library(rpc_bugatone_proxy SHARED
        rpc_bugatone_proxy/rpc_bugatone_proxy.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h)
target_include_directories(rpc_bugatone_proxy PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        )
target_link_libraries(rpc_bugatone_proxy proto rpc_server)
target_compile_definitions(rpc_bugatone_proxy PRIVATE
        REAL_LIB_NAME="libbugatone.so"
        )
set_target_properties(rpc_bugatone_proxy PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
set_target_properties(rpc_bugatone_proxy PROPERTIES INSTALL_RPATH "$ORIGIN")


# Daemon RPC proxy library
project(rpc_authdemo_proxy)
add_library(rpc_authdemo_proxy SHARED
        rpc_bugatone_proxy/rpc_bugatone_proxy.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h)
target_include_directories(rpc_authdemo_proxy PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        )
target_link_libraries(rpc_authdemo_proxy proto rpc_server)
target_compile_definitions(rpc_authdemo_proxy PRIVATE
        REAL_LIB_NAME="libauthdemo.so"
        )
set_target_properties(rpc_authdemo_proxy PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
set_target_properties(rpc_authdemo_proxy PROPERTIES INSTALL_RPATH "$ORIGIN")


# Daemon RPC proxy library
project(rpc_mobileproduct2_proxy)
add_library(rpc_mobileproduct2_proxy SHARED
        rpc_bugatone_proxy/rpc_bugatone_proxy.cpp
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h)
target_include_directories(rpc_mobileproduct2_proxy PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        )
target_link_libraries(rpc_mobileproduct2_proxy proto rpc_server)
target_compile_definitions(rpc_mobileproduct2_proxy PRIVATE
        REAL_LIB_NAME="libmobileproduct2.so"
        RUN_CREATE_BUGATONE_API_ON_INIT=1
        USE_REAL_NAME_ON_ANDROID=1
        )
set_target_properties(rpc_mobileproduct2_proxy PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
set_target_properties(rpc_mobileproduct2_proxy PROPERTIES INSTALL_RPATH "$ORIGIN")


# Daemon RPC main library
project(rpc_bugatone_main)
add_library(rpc_bugatone_main SHARED
        rpc_bugatone_proxy/rpc_bugatone_main.cpp)
target_include_directories(rpc_bugatone_main PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        )
target_compile_definitions(rpc_bugatone_main PRIVATE
        )
if(MY_BUILD_ANDROID)
    target_link_libraries(rpc_bugatone_main android log)
endif(MY_BUILD_ANDROID)


# Daemon RPC main executable - so not really daemon
project(rpc_bugatone_main_exec)
add_executable(rpc_bugatone_main_exec
        rpc_bugatone_proxy/rpc_bugatone_main.cpp)
target_include_directories(rpc_bugatone_main_exec PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        )
target_compile_definitions(rpc_bugatone_main_exec PRIVATE
        RPC_BUGATONE_MAIN_EXECUTABLE=1
        )
if(MY_BUILD_ANDROID)
    target_link_libraries(rpc_bugatone_main_exec android)
else(MY_BUILD_ANDROID)
    target_link_libraries(rpc_bugatone_main_exec dl)
endif(MY_BUILD_ANDROID)


# RPC benchmark so
project(grpc_test)
add_library(grpc_test SHARED
        ../3rdparty/device_communication_common/rpc_bindings/bugarpc.h
        rpc_test/benchmark_executor.cpp
        rpc_test/benchmark_executor.h)
target_include_directories(grpc_test PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ${PROTO_SRC_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ../3rdparty/device_communication_common/
        ../3rdparty/nlohmann/include/
        )
target_link_libraries(grpc_test proto rpc_server)
