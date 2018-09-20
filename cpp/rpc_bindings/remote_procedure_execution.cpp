#include "remote_procedure_execution.h"
#include "marshallers.h"

MarshaledObject StandardRemoteProcedureExecutor::delegateProcedure(std::string procedureName, const MarshaledObject &params) {
    if (procedureName == "_rpc_get_version") {
        return marshal(getVersion());
    } if (procedureName == "_rpc_echo") {
        return rpc_echo(params);
    } if (procedureName == "_rpc_echo_push") {
        return rpc_echo_push(params);
    } if (procedureName == "_rpc_echo_pop") {
        return rpc_echo_pop(params);
    } else {
        return executeProcedure(procedureName, params);
    }
}

MarshaledObject StandardRemoteProcedureExecutor::rpc_echo(const MarshaledObject &params) {
    return params;
}

MarshaledObject StandardRemoteProcedureExecutor::rpc_echo_push(const MarshaledObject &params) {
    stack.push(params);
    return marshal(std::string("OK"));
}

MarshaledObject StandardRemoteProcedureExecutor::rpc_echo_pop(const MarshaledObject &params) {
    if (stack.empty())
        return marshal(std::string());
    MarshaledObject mo = stack.top();
    stack.pop();
    return mo;
}
