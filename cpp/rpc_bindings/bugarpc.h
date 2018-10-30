//
// This file contains the executor's interface needed to be implemented in order to receive calls from python.
// Moreover, it also includes the declaration of server factories that can be used in combination with
// instances of executors.
// Using RPC should be as simple as including this file, and a compiled shared library that includes an implementation
// for the desired server factories, in your project.
//
// The file is meant to remain unchanged, except for the possible additions of factory declarations at its bottom.
//

#ifndef CPP_BUGARPC_H
#define CPP_BUGARPC_H

#include <string>
#include <vector>
#include <memory>


/**
 * Buffer type (e.g. for passing parametes).
 */
using Buffer = std::string;

/**
 * Interface to be implemented and passed to RemoteProcedureServer.
 *
 * In order to receive messages from python, implement this interface, create an instance,
 * and pass it to a RemoteProcedureServer.
 *
 * Notes:
 *  Procedure names beginning with "_rpc_" are reserved for server implementers, and therefore must not be used.
 *
 * Example:
 *  The following class implementation adds a procedure called "stringSize" that returns the size of strings.
 *
 *  ```
 *  class MyExecutor : public IRemoteProcedureExecutor {
 *      Buffer executeProcedure(const std::string &procedureName, const Buffer &params) {
 *          if (procedureName == "stringSize") {
 *              return std::to_string(params.size());
 *          } else {
 *              throw std::runtime_error("No such procedure");
 *          }
 *      }
 *      std::string getVersion() override { return "1.0"; }
 *  }
 *  ```
 *
 *  You can use this class by creating a server and passing the executor instance:
 *
 *  ```
 *      createBugaGRPCServer()->listen(MyExecutor(), 50100);
 *  ```
 *
 *  You can also use an existing So Loader, defined below.
 */
class IRemoteProcedureExecutor {
public:
    /**
     * This method will be called by the RemoteProcedureServer on each sent message.
     *
     * Notes:
     *  Procedure names beginning with "_rpc_" are reserved for server implementers, and therefore must not be used.
     *
     * @param procedureName Name of procedure called, not beginning with "_rpc_".
     * @param params The Buffer sent from python.
     * @return Buffer representing return value to be sent back to python.
     */
    virtual Buffer executeProcedure(const std::string &procedureName, const Buffer &params) = 0;

    /**
     * @return String representing the version of the executor.
     */
    virtual std::string getVersion() = 0; // Get current executor version

    virtual ~IRemoteProcedureExecutor() = default;
};


/**
 * Alias to make the `rpc_id` requirement a bit more explicit.
 * Doesn't really do anything, developers can use `int` instead in their code.
 */
using int_between_30000_and_50000 = int;


/**
 * Public interface to RPC servers. This is implemented by the library owners and used by the library clients.
 *
 * All server implementations have the following requirements:
 *
 *      1. If python calls the procedure "_rpc_get_version", server must call `getVersion` on the executor
 *          instance and return the result.
 *      2. If python calls the procedure "_rpc_stop", server must call its `stop` method.
 */
class IRemoteProcedureServer {
public:
    /**
     * Start listening on given port to messages from python and pass them along to the executor.
     *
     * Notes:
     *  This function blocks until `stop` is called.
     *
     * @param listener Executor implementation that responds to messages.
     * @param rpc_id Unique identifier for your executor to listen to, must be between 30,000 and 50,000.
     * @param wait Whether to block waiting or to return immediately. It this is false, you need to call wait() later on.
     */
    virtual void listen(IRemoteProcedureExecutor &executor, int_between_30000_and_50000 rpc_id, bool wait) = 0;

    /**
     * Block waiting in a server loop. This should be used if listen() was called with wait==false.
     * Could be from a different thread than listen().
     */
    virtual void wait() = 0;

    /**
     * Stop listening, makes the listen thread return.
     */
    virtual void stop() = 0;

    virtual ~IRemoteProcedureServer() = default;
};


/**
 * This error can be thrown in the executor and it will be raised as a RpcError on the caller side.
 */
struct RpcError : public std::runtime_error {
    explicit RpcError(const std::string &msg) : std::runtime_error(msg) {}
};

/**
 * .so's to be loaded by So Loaders, defined below, must include a function `create_executor`, which is declared `extern "C"`,
 * and is of the following type. So Loaders will call this function and pass the result on to a server.
 */
using CreateExecutorFunc = std::unique_ptr<IRemoteProcedureExecutor> (*)();

/**
 * Definition: So Loader
 *
 * A combination of python and android code that includes a python client factory implementation. The factory's
 * `install` method sends a compiled .so to the phone, and subsequent calls to `create_connection` load the .so on the
 * phone and call the function `create_executor` that must exist in the .so.
 *
 * So Loaders can have additional requirements on the .so's they handle.
 *
 * So Loaders in the works:
 *  1. Java gRPC So Loader - a java app that simply loads .so's, calls their `create_executor`, and starts a gRPC
 *      server that passes messages to the created executor.
 *
 *  2. libbugatone gRPC So Loader - a mechanism to replace the libbugatone.so that is loaded by the Oppo daemon. The
 *      .so's it handles must have an additional function called `createBugatoneApi`, as defined in
 *      `mobileproduct/src/bugatone_api/ibugatone_api.h`. When the daemon loads bugatone, this method will be called,
 *      and then `create_executor` will be called (from the same thread), and then the `createBugatoneApi` return
 *      value will be passed back to the daemon.
 *      The mechanism of sending the libbugatone.so is still yet to be defined. But as long as it satisfies the
 *      requirement that writing and compiling a `libbugatone.so`, simply with an extra function `create_executor`,
 *      is all that it takes to have RPC - we are doing good.
 */


#endif //CPP_BUGARPC_H
