#include <iostream>

#include <memory>
#include <string>

#include "rpc_impl/buga_grpc_server.h"
#include "rpc_impl/buga_rpc_executor.h"

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    GRemoteProcedureServer server(server_address);
    BugaRpcExecutor bugaRpcExecutor;
    server.listen(bugaRpcExecutor);
}

int main(int argc, char **argv) {
    RunServer();

    return 0;
}
