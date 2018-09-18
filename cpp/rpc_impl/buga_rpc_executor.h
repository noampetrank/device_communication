#ifndef CPP_BUGA_RPC_EXECUTOR_H
#define CPP_BUGA_RPC_EXECUTOR_H

#include "../rpc_bindings/remote_procedure_execution.h"

class BugaRpcExecutor : public StandardRemoteProcedureExecutor {
protected:
    virtual void onStart(const MarshaledObject &params) override {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop(const MarshaledObject &params) override {} // Connection is about to close.

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshaledObject executeProcedure(std::string procedureName, const MarshaledObject &params) override;
};

#endif //CPP_BUGA_RPC_EXECUTOR_H
