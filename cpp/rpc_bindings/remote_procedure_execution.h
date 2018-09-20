#ifndef CPP_REMOTE_PROCEDURE_EXECUTION_H
#define CPP_REMOTE_PROCEDURE_EXECUTION_H

#include <string>
#include <memory>
#include <stack>

using Buffer = std::string;
using MarshaledObject = std::shared_ptr<Buffer>;

template <class T>
MarshaledObject marshal(const T &p);

template <class T>
T unmarshal(const MarshaledObject &buf);


class IRemoteProcedureExecutor {
public:
    virtual MarshaledObject delegateProcedure(std::string procedureName, const MarshaledObject &params) = 0; // Delegate a procedure call from the caller
    virtual std::string getVersion() = 0; // Get current executor version

    virtual ~IRemoteProcedureExecutor() = default;
};


class StandardRemoteProcedureExecutor : public IRemoteProcedureExecutor {
public:
    virtual MarshaledObject delegateProcedure(std::string procedureName, const MarshaledObject &params) final override;
    virtual std::string getVersion() override { return "0.0"; }

protected:

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshaledObject executeProcedure(std::string procedureName, const MarshaledObject &params) = 0;

private:
    virtual MarshaledObject rpc_echo(const MarshaledObject &params) final;
    virtual MarshaledObject rpc_echo_push(const MarshaledObject &params) final;
    virtual MarshaledObject rpc_echo_pop(const MarshaledObject &params) final;

    std::stack<MarshaledObject> stack;
};


class IRemoteProcedureServer {
public:
    // Listens; calls delegate when stuff arrives
    virtual void listen(IRemoteProcedureExecutor &listener, bool wait = true) = 0;
    virtual void wait() = 0;
    virtual void stop() = 0;
    virtual ~IRemoteProcedureServer() = default;
};



// TODO add streaming API

#endif //CPP_REMOTE_PROCEDURE_EXECUTION_H
