#include "buga_rpc_executor.h"

MarshaledObject BugaRpcExecutor::executeProcedure(std::string procedureName, const MarshaledObject &params) {
    //TODO implement
    return std::make_shared<std::string>("OK: " + *params);
}
