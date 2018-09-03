#ifndef CPP_BUGA_RPC_EXECUTOR_H
#define CPP_BUGA_RPC_EXECUTOR_H

#include "../rpc_bindings/remote_procedure_execution.h"

class BugaRpcExecutor : public StandardRemoteProcedureExecutor {
protected:
    virtual void onStart(const MarshalledObject &params) override {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop(const MarshalledObject &params) override {} // Connection is about to close.

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledObject executeProcedure(std::string procedureName, const MarshalledObject &params) override;
};

#endif //CPP_BUGA_RPC_EXECUTOR_H
