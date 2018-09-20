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

    IRemoteProcedureExecutor &getListener() { return listener; }

    Status call(ServerContext* context,
                const GRequest* req,
                GResponse* res) override {
        MarshaledObject arg = std::make_shared<std::string>(req->buf());
        MarshaledObject ret = listener.delegateProcedure(req->name(), arg);
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

void GRemoteProcedureServer::listen(IRemoteProcedureExecutor &listener, bool wait) {
    service = std::make_unique<BugaGRpcServiceImpl>(listener);
    if (!service.get())
        throw GRPCServerError("Service object is null");

    ServerBuilder builder;
    // Listen on the given address without any authentication mechanism.
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    // Register "service" as the instance through which we'll communicate with
    // clients. In this case it corresponds to an *synchronous* service.
    builder.RegisterService(service.get());
    // Set max message size to 1Gb
    const int max_message_size = 1024*1024*1024;
    builder.SetMaxReceiveMessageSize(max_message_size);
    builder.SetMaxSendMessageSize(max_message_size);
    std::cout << max_message_size << std::endl;
    // Finally assemble the server.
    server = builder.BuildAndStart();
    std::cout << "Server listening on " << server_address << std::endl;

    if (!server.get())
        throw GRPCServerError("Server object is null");

    if (wait) {
        // Wait for the server to shutdown. Note that some other thread must be
        // responsible for shutting down the server for this call to ever return.
        server->Wait();
    }
}

void GRemoteProcedureServer::wait() {
    if (!server.get())
        throw GRPCServerError("Server object is null");
    server->Wait();
}

void GRemoteProcedureServer::stop() {
    if (!server.get())
        throw GRPCServerError("Server object is null");
    server->Shutdown();
}
