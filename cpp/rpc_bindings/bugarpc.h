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
using Buffer = std::vector<char>;


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
 *      std::string executeProcedure(std::string procedureName, std::string params) {
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
     * @param params The string sent from python.
     * @return String representing return value to be sent back to python.
     */
    virtual std::string executeProcedure(const std::string &procedureName, const Buffer &params) = 0;

    /**
     * @return String representing the version of the executor.
     */
    virtual std::string getVersion() = 0; // Get current executor version

    virtual ~IRemoteProcedureExecutor() = default;
};


// Alias to make the `rpc_id` requirement a bit more explicit.
// Doesn't really do anything, developers can use `int` instead in their code.
using int_between_30000_and_50000 = int;


/**
 * Public interface to RPC servers. This is implemented by the library owners and used by the library clients.
 * See below for creating instances of specific implementations.
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
     */
    virtual void listen(IRemoteProcedureExecutor &executor, int_between_30000_and_50000 rpc_id) = 0;

    /**
     * Stop listening, makes the listen thread return.
     */
    virtual void stop() = 0;

    virtual ~IRemoteProcedureServer() = default;
};


//region Server Factories

/**
 * All server implementations have the following requirements:
 *
 *      1. If python calls the procedure "_rpc_get_version", server must call `getVersion` on the executor
 *          instance and return the result.
 *      2. If python calls the procedure "_rpc_stop", server must call its `stop` method.
 *
 */

/**
 * Factory that creates a server instance that uses gRPC for communication.
 */
std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer();

//endregion

#endif //CPP_BUGARPC_H
