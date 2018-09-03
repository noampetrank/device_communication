#include "remote_procedure_execution.h"
#include "marshallers.h"

MarshalledObject StandardRemoteProcedureExecutor::delegateProcedure(std::string procedureName, const MarshalledObject &params) {
    if (procedureName == "_rpc_get_version") {
        return marshal(getVersion());
    } if (procedureName == "_rpc_echo") {
        return rpc_echo(params);
    } if (procedureName == "_rpc_start") {
        onStart(params);
        return MarshalledObject();
    } if (procedureName == "_rpc_stop") {
        onStop(params);
        return MarshalledObject();
    } else {
        return executeProcedure(procedureName, params);
    }
}

MarshalledObject StandardRemoteProcedureExecutor::rpc_echo(const MarshalledObject &params) {
    return params;
}

