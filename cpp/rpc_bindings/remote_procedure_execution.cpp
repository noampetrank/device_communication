#include "remote_procedure_execution.h"
#include "marshallers.h"

MarshalledObject StandardRemoteProcedureExecutor::delegateProcedure(std::string procedureName, const MarshalledObject &params) {
    if (procedureName == "_rpc_get_version") {
        return marshal(getVersion());
    } if (procedureName == "_rpc_echo") {
        return rpc_echo(params);
    } if (procedureName == "_rpc_echo_push") {
        return rpc_echo_push(params);
    } if (procedureName == "_rpc_echo_pop") {
        return rpc_echo_pop(params);
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

MarshalledObject StandardRemoteProcedureExecutor::rpc_echo_push(const MarshalledObject &params) {
    stack.push(params);
    return marshal(std::string("OK"));
}

MarshalledObject StandardRemoteProcedureExecutor::rpc_echo_pop(const MarshalledObject &params) {
    if (stack.empty())
        return marshal(std::string("Empty"));
    MarshalledObject mo = stack.top();
    stack.pop();
    return mo;
}
