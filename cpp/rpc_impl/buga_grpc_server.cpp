#include "buga_grpc_server.h"

#include <grpcpp/grpcpp.h>
#include "buga_rpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using buga_rpc::GRequest;
using buga_rpc::GResponse;
using buga_rpc::DeviceRpc;

// Logic and data behind the server's behavior.
class BugaGRpcServiceImpl final : public GRpcServiceImpl {
    IRemoteProcedureExecutor &listener;
public:
    explicit BugaGRpcServiceImpl(IRemoteProcedureExecutor &listener) : listener(listener) {}

    Status call(ServerContext* context,
                const GRequest* req,
                GResponse* res) override {
        MarshalledObject arg = std::make_shared<std::string>(req->buf());
        MarshalledObject ret = listener.delegateProcedure(req->name(), arg);
        res->set_buf(*ret);
        return Status::OK;
    }

    Status grpc_echo(ServerContext *context,
                     const GRequest *req,
                     GResponse *res) override {
        res->set_buf(req->buf());
        return Status::OK;
    }
};


GRemoteProcedureServer::GRemoteProcedureServer(std::string server_address)
    : server_address(std::move(server_address)) { }

GRemoteProcedureServer::~GRemoteProcedureServer() = default;

void GRemoteProcedureServer::listen(IRemoteProcedureExecutor &listener) {
    service = std::make_unique<BugaGRpcServiceImpl>(listener);

    ServerBuilder builder;
    // Listen on the given address without any authentication mechanism.
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    // Register "service" as the instance through which we'll communicate with
    // clients. In this case it corresponds to an *synchronous* service.
    builder.RegisterService(service.get());
    // Finally assemble the server.
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    // Wait for the server to shutdown. Note that some other thread must be
    // responsible for shutting down the server for this call to ever return.
    server->Wait();
}
