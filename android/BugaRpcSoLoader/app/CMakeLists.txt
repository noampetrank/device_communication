# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

cmake_minimum_required(VERSION 3.4.1)


# Creates and names a library, sets it as either STATIC
# or SHARED, and provides the relative paths to its source code.
# You can define multiple libraries, and CMake builds them for you.
# Gradle automatically packages shared libraries with your APK.

add_library( # Sets the name of the library.
        native-lib

        # Sets the library as a shared library.
        SHARED

        # Provides a relative path to your source file(s).
        src/main/cpp/native-lib.cpp)

# Searches for a specified prebuilt library and stores the path as a
# variable. Because CMake includes system libraries in the search path by
# default, you only need to specify the name of the public NDK library
# you want to add. CMake verifies that the library exists before
# completing its build.

find_library( # Sets the name of the path variable.
        log-lib

        # Specifies the name of the NDK library that
        # you want CMake to locate.
        log)

# Specifies libraries CMake should link to your target library. You
# can link multiple libraries, such as libraries you define in this
# build script, prebuilt third-party libraries, or system libraries.

target_link_libraries( # Specifies the target library.
        native-lib

        # Links the target library to the log library
        # included in the NDK.
        ${log-lib})


# Build the device comm .so's and copy them to the right place
set(DEVICE_COMM_PROJECT_DIR /home/buga/device_communication/cpp)
set(DEVICE_COMM_LIBS_DIR ${DEVICE_COMM_PROJECT_DIR}/lib/arm64/Release)
set(TARGET_LIBS_DIR src/main/jniLibs/arm64-v8a/)

add_custom_target(rpc_satellite_sos
        COMMAND echo Building device comm...
        COMMAND ${DEVICE_COMM_PROJECT_DIR}/make.py android
        COMMAND mkdir -p ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND mkdir -p ${DEVICE_COMM_LIBS_DIR}
        WORKING_DIRECTORY ${DEVICE_COMM_PROJECT_DIR}
        )

add_custom_target(buga_rpc_libs
        COMMAND echo Copying device comm files...
        COMMAND cp ${DEVICE_COMM_LIBS_DIR}/libproto.so ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND cp ${DEVICE_COMM_LIBS_DIR}/librpc_server.so ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND cp ${DEVICE_COMM_LIBS_DIR}/librpc_so_loader.so ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND cp ${DEVICE_COMM_LIBS_DIR}/librpc_so_loader_main.so ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND echo Done with device comm.
        WORKING_DIRECTORY ${DEVICE_COMM_PROJECT_DIR}
        COMMENT Building device comm)
add_dependencies(buga_rpc_libs
        rpc_satellite_sos)

add_custom_target(ndk_libs
        COMMAND echo Copying NDK stuff...
        COMMAND cp ${ANDROID_STL_PATH}/libs/arm64-v8a/libc++_shared.so ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET_LIBS_DIR}
        COMMAND echo Done copying NDK stuff.
        COMMENT Copying NDK stuff)
add_dependencies(ndk_libs
        rpc_satellite_sos)

add_dependencies(native-lib buga_rpc_libs ndk_libs)


get_cmake_property(_variableNames VARIABLES)
list (SORT _variableNames)
foreach (_variableName ${_variableNames})
    message(STATUS "${_variableName}=${${_variableName}}")
endforeach()