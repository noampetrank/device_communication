#include "buga_echo_executor.h"

Buffer BugaEchoExecutor::executeProcedure(const std::string &procedureName, const Buffer &params) {
    if (procedureName == "rpc_echo") {
        return params;
    } if (procedureName == "rpc_echo_push") {
        stack.push(params);
        return "OK";
    } if (procedureName == "rpc_echo_pop") {
        if (stack.empty())
            return "";
        auto mo = stack.top();
        stack.pop();
        return mo;
    } else {
        throw RPCServerError("Wrong procedure name " + procedureName);
    }
}
