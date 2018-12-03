#ifndef RPC_SO_LOADER_BUGA_ECHO_EXECUTOR_H
#define RPC_SO_LOADER_BUGA_ECHO_EXECUTOR_H

#include "rpc_bindings/bugarpc.h"
#include <stack>

class BugaEchoExecutor : public IRemoteProcedureExecutor {
public:
    Buffer executeProcedure(const std::string &procedureName, const Buffer &params) override;
    std::string getVersion() override { return "1.0"; }
protected:
    std::stack<Buffer> stack;
};

#endif //RPC_SO_LOADER_BUGA_ECHO_EXECUTOR_H
