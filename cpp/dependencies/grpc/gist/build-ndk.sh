#!/bin/sh -e
##
# Largely derived from a combination of:
#  * Other scripts in .gitlab-ci.yml
#  * https://developer.android.com/ndk/guides/standalone_toolchain.html#building_open_source_projects_using_standalone_toolchains
#  * https://github.com/grpc/grpc/blob/v1.7.3/INSTALL.md
#
# The Makefile has the following instructions:
#
#   The steps for cross-compiling are as follows:
#   First, clone and make install of grpc using the native compilers for the host.
#   Also, install protoc (e.g., from a package like apt-get)
#   Then clone a fresh grpc for the actual cross-compiled build
#   Set the environment variable GRPC_CROSS_COMPILE to true
#   Set CC, CXX, LD, LDXX, AR, and STRIP to the cross-compiling binaries
#   Also set PROTOBUF_CONFIG_OPTS to indicate cross-compilation to protobuf (e.g.,
#    PROTOBUF_CONFIG_OPTS="--host=arm-linux --with-protoc=/usr/local/bin/protoc" )
#   Set HAS_PKG_CONFIG=false
#   To build tests, go to third_party/gflags and follow its ccmake instructions
#   Make sure that you enable building shared libraries and set your prefix to
#   something useful like /usr/local/cross
#   You will also need to set GRPC_CROSS_LDOPTS and GRPC_CROSS_AROPTS to hold
#   additional required arguments for LD and AR (examples below)
#   Then you can do a make from the cross-compiling fresh clone!
#
##

set -x
set -e

: ${ANDROID_NDK="/path/to/ndk"}
: ${NDK_TOOLCHAIN="${HOME}/android-arm64-toolchain"}
: ${PROJECT_DIR="${HOME}/build-grpc-android"}

GRPC_VERSION="1.7.3"
PROTOC_VERSION="3.4.0"
ANDROID_VERSION="24"
STL="libc++"
HOST="aarch64-linux-android"
INSTALL_DIR=${PROJECT_DIR}/ndk-install
PROTOC_DIR=${PROJECT_DIR}/protoc-${PROTOC_VERSION}
GRPC_SRC_DIR_HOST="${PROJECT_DIR}/grpc-host"
GRPC_SRC_DIR_ARM64="${PROJECT_DIR}/grpc-arm64"

mkdir -p ${INSTALL_DIR}

### 1) Clone, make and install on host OS
if [ ! -d ${GRPC_SRC_DIR_HOST} ]; then
    git clone -b v${GRPC_VERSION} https://github.com/grpc/grpc ${GRPC_SRC_DIR_HOST}
    cd ${GRPC_SRC_DIR_HOST}
    GIT_SSL_NO_VERIFY=1 git submodule update --init
    make
fi

### 2) Install protoc binary

# protoc executable is required to build tests, but the one we're building is for arm64. Download Linux x86_64 version.
# Assumes this script is being run on Linux x86_64.
if [ ! -d ${PROTOC_DIR} ]; then
    curl -O -L -k https://github.com/google/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip
    unzip protoc-${PROTOC_VERSION}-linux-x86_64.zip -d ${PROTOC_DIR}
fi

### 3) Clone, make and install for target OS

if [ ! -d ${GRPC_SRC_DIR_ARM64} ]; then
    git clone -b v${GRPC_VERSION} https://github.com/grpc/grpc ${GRPC_SRC_DIR_ARM64}
    cd ${GRPC_SRC_DIR_ARM64}
    GIT_SSL_NO_VERIFY=1 git submodule update --init
    # Taken from https://github.com/grpc/grpc/pull/13011/commits/819ec5069b050c21d3cbaa69289b89dfc7080979
    # Prevent compilation errors in c-ares caused by the fact that Android doesn't have getservbyport_r function
    patch ${GRPC_SRC_DIR_ARM64}/third_party/cares/config_linux/ares_config.h ${PROJECT_DIR}/android_ares_config.patch
    # Patch Makefile to fix the following problems:
    # * Android can't link against rt or pthread because they are already included in its Bionic C standard library
    # * Allow protoc to find the grpc plugins it requires, built for the (x86) host OS rather than the (arm64) target
    patch ${GRPC_SRC_DIR_ARM64}/Makefile ${PROJECT_DIR}/makefile.patch
fi

${ANDROID_NDK}/build/tools/make_standalone_toolchain.py \
    --arch arm64 \
    --api ${ANDROID_VERSION} \
    --stl=${STL} \
    --install-dir=${NDK_TOOLCHAIN} \
    --force

cd ${GRPC_SRC_DIR_ARM64}

export AR=${NDK_TOOLCHAIN}/bin/${HOST}-ar
export CC=${NDK_TOOLCHAIN}/bin/${HOST}-clang
export CXX=${NDK_TOOLCHAIN}/bin/${HOST}-clang++
export LD=${NDK_TOOLCHAIN}/bin/${HOST}-clang++
export LDXX=${NDK_TOOLCHAIN}/bin/${HOST}-clang++
export RANLIB=${NDK_TOOLCHAIN}/bin/${HOST}-ranlib
export STRIP="${NDK_TOOLCHAIN}/bin/${HOST}-strip --strip-unneeded"

export SYSTEM=Linux
export GRPC_CROSS_COMPILE=true
export GRPC_CROSS_AROPTS="rcs --target=elf64-littleaarch64"
export PROTOBUF_CONFIG_OPTS="--host=${HOST} --with-protoc=${PROTOC_DIR}/bin/protoc"
export PROTOBUF_LDFLAGS_EXTRA="-llog"  # Android logging library
export PROTOC="${PROTOC_DIR}/bin/protoc"
export PROTOC_PLUGINS_DIR="${GRPC_SRC_DIR_HOST}/bins/opt"
export HAS_PKG_CONFIG=false

# -fPIE, -fPIC, -pie are recommended by Android (https://developer.android.com/ndk/guides/standalone_toolchain.html)
# -w allows us to build where we can't resolve the warnings
export CFLAGS="-fPIE -fPIC -w"
export LDFLAGS="-v -Wl,-pie"

export prefix=${INSTALL_DIR}

make install_c install_cxx install-certs

cd ${INSTALL_DIR}
tar -cJf ${PROJECT_DIR}/grpc-${GRPC_VERSION}-android-arm64-v8a.tar.xz *

cd ${GRPC_SRC_DIR_HOST}/bins/opt
tar -cJf ${PROJECT_DIR}/grpc_cpp_plugin-${GRPC_VERSION}-android-arm64-v8a.tar.xz grpc_cpp_plugin