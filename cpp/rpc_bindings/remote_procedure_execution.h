#ifndef CPP_REMOTE_PROCEDURE_EXECUTION_H
#define CPP_REMOTE_PROCEDURE_EXECUTION_H

#include <string>
#include <memory>
#include <stack>

using Buffer = std::string;
using MarshalledObject = std::shared_ptr<Buffer>;

template <class T>
MarshalledObject marshal(const T &p);

template <class T>
T unmarshal(const MarshalledObject &buf);


class IRemoteProcedureExecutor {
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) = 0; // Delegate a procedure call from the caller
    virtual std::string getVersion() = 0; // Get current executor version
    virtual ~IRemoteProcedureExecutor() = default;
};


class StandardRemoteProcedureExecutor : public IRemoteProcedureExecutor {
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) final override;
    virtual std::string getVersion() override { return "0.0"; }

protected:
    virtual void onStart(const MarshalledObject &params) {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop(const MarshalledObject &params) {} // Connection is about to close.

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledObject executeProcedure(std::string procedureName, const MarshalledObject &params) = 0;

private:
    virtual MarshalledObject rpc_echo(const MarshalledObject &params) final;
    virtual MarshalledObject rpc_echo_push(const MarshalledObject &params) final;
    virtual MarshalledObject rpc_echo_pop(const MarshalledObject &params) final;

    std::stack<MarshalledObject> stack;
};


class IRemoteProcedureServer {
public:
    // Listens; calls delegate when stuff arrives
    virtual void listen(IRemoteProcedureExecutor &listener, bool wait = true) = 0;
    virtual ~IRemoteProcedureServer() = default;
};



// TODO add streaming API

#endif //CPP_REMOTE_PROCEDURE_EXECUTION_H
