#ifndef CPP_BUGA_GRPC_SERVER_H
#define CPP_BUGA_GRPC_SERVER_H

#include "../rpc_bindings/remote_procedure_execution.h"
#include "buga_rpc.grpc.pb.h"

using GRpcServiceImpl = buga_rpc::DeviceRpc::Service;

class GRemoteProcedureServer : public IRemoteProcedureServer {
    std::unique_ptr<GRpcServiceImpl> service;
    std::string server_address;
public:
    GRemoteProcedureServer(std::string server_address);
    ~GRemoteProcedureServer();
    virtual void listen(IRemoteProcedureExecutor &listener, bool wait = true) override;
};

#endif //CPP_BUGA_GRPC_SERVER_H
