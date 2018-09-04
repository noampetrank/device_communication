#include "buga_rpc_executor.h"

MarshalledObject BugaRpcExecutor::executeProcedure(std::string procedureName, const MarshalledObject &params) {
    //TODO implement
    return std::make_shared<std::string>("OK: " + *params);
}
