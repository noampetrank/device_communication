#include "rpc_bindings/bugarpc.h"
#include "buga_rpc.grpc.pb.h"

#include <iostream>
#include <grpcpp/grpcpp.h>
#include "buga_rpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using buga_rpc::GRequest;
using buga_rpc::GResponse;
using buga_rpc::DeviceRpc;


// region Server declaration

using GRpcServiceImpl = buga_rpc::DeviceRpc::Service;

/**
 * This is the gRPC server, which receives calls from the remote client.
 */
class GRemoteProcedureServer : public IRemoteProcedureServer {
public:
    void listen(IRemoteProcedureExecutor &listener, int_between_30000_and_50000 rpcId, bool wait) override;
    void wait() override;
    void stop() override;

private:
    std::unique_ptr<GRpcServiceImpl> service;
    std::unique_ptr<grpc::Server> server;
};

// endregion


// region Service

/**
 * This is the gRPC "service" implementation (https://grpc.io/img/landing-2.svg), which handles calls on the server.
 * It's a thin translation layer from gRPC "service" to Buga "executor".
 */
class BugaGRpcServiceImpl final : public GRpcServiceImpl {
public:
    BugaGRpcServiceImpl(IRemoteProcedureExecutor &listener, GRemoteProcedureServer *parentServer) : listener(listener), parentServer(parentServer) {}

    Status call(ServerContext* context,
                const GRequest* req,
                GResponse* res) override;

    Status grpc_echo(ServerContext *context,
                     const GRequest *req,
                     GResponse *res) override;

private:
    IRemoteProcedureExecutor &listener;
    GRemoteProcedureServer * const parentServer;

    bool handleServerRpc(const std::string &name, const Buffer &params, Buffer &ret);
};

Status BugaGRpcServiceImpl::call(ServerContext *context, const GRequest *req, GResponse *res) {
    const std::string &name = req->name();
    const Buffer &params = req->buf();

    Buffer ret;
    if (!handleServerRpc(name, params, ret)) {
        try {
            ret = listener.executeProcedure(name, params);
        } catch (RpcError &ex) {
            return Status(grpc::UNKNOWN, std::string("RPC error in executeProcedure: ") + ex.what());
        } catch (std::runtime_error &ex) {
            return Status(grpc::UNKNOWN, std::string("Runtime error in executeProcedure: ") + ex.what());
        } catch (...) {
            return Status(grpc::UNKNOWN, std::string("Exception in executeProcedure"));
        }
    }
    res->set_buf(ret);
    return Status::OK;
}

Status BugaGRpcServiceImpl::grpc_echo(ServerContext *context, const GRequest *req, GResponse *res) {
    res->set_buf(req->buf());
    return Status::OK;
}

bool BugaGRpcServiceImpl::handleServerRpc(const std::string &name, const Buffer &params, Buffer &ret) {
    if (name == "_rpc_get_version") {
        ret = listener.getVersion();
        return true;
    } else if (name == "_rpc_stop") {
        // TODO make this work
        parentServer->stop();
        return true;
    }
    return false;
}

// endregion


// region Server

void GRemoteProcedureServer::listen(IRemoteProcedureExecutor &listener, int_between_30000_and_50000 rpcId, bool wait) {
    service = std::make_unique<BugaGRpcServiceImpl>(listener, this);
    if (!service)
        throw RpcError("Service object is null");

    ServerBuilder builder;
    // Listen on the given address without any authentication mechanism.
    std::string server_address = "0.0.0.0:" + std::to_string(rpcId);
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    // Register "service" as the instance through which we'll communicate with
    // clients. In this case it corresponds to an *synchronous* service.
    builder.RegisterService(service.get());
    // Set max message size to 1Gb
    const int max_message_size = 1024*1024*1024;
    builder.SetMaxReceiveMessageSize(max_message_size);
    builder.SetMaxSendMessageSize(max_message_size);
    std::cout << "Server max message size is " << max_message_size << " bytes" << std::endl;
    // Finally assemble the server.
    server = builder.BuildAndStart();
    std::cout << "Server listening on " << server_address << std::endl;

    if (!server)
        throw RpcError("Server object is null");

    if (wait) {
        // Wait for the server to shutdown. Note that some other thread must be
        // responsible for shutting down the server for this call to ever return.
        server->Wait();
    }
}

void GRemoteProcedureServer::wait() {
    if (!server)
        throw RpcError("Server object is null");
    server->Wait();
}

void GRemoteProcedureServer::stop() {
    if (!server)
        throw RpcError("Server object is null");
    server->Shutdown();
}


/**
 * Factory that creates a server instance that uses gRPC for communication.
 */
std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer() {
    return std::make_unique<GRemoteProcedureServer>();
}

// endregion
