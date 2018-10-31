if (MY_BUILD_ANDROID)
    set(APP_STL c++_shared)
    set(CMAKE_ANDROID_STL_TYPE c++_shared)
    set(CMAKE_ANDROID_ARCH_ABI arm64-v8a)
    set(CMAKE_SYSTEM_NAME Android)
    set(CMAKE_ANDROID_STANDALONE_TOOLCHAIN /tmp/android-toolchain)
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
add_executable(cpp
        demo_main.cpp
        rpc_bindings/remote_procedure_execution.cpp
        rpc_impl/buga_rpc_executor.cpp
        rpc_impl/buga_rpc_executor.h
        rpc_impl/buga_grpc_server.cpp
        rpc_impl/buga_grpc_server.h
        rpc_bindings/marshallers.cpp
        rpc_bindings/marshallers.h)
target_include_directories(cpp PRIVATE
        ${CMAKE_CURRENT_BINARY_DIR}
        ../3rdparty/nlohmann/include/
)

target_link_libraries(cpp proto)