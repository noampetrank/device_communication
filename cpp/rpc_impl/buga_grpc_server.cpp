#include "rpc_bindings/bugarpc.h"
#include "buga_rpc.grpc.pb.h"

#include <iostream>
#include <cstdio>
#include <grpcpp/grpcpp.h>
#include <thread>
#include "buga_rpc.pb.h"

#include "utils/rpc_log.h"


using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using buga_rpc::GRequest;
using buga_rpc::GResponse;
using buga_rpc::DeviceRpc;
using buga_rpc::DeviceRpcStreaming;
using buga_rpc::GBuffer;


// region Server declaration

using GRpcServiceImpl = buga_rpc::DeviceRpc::Service;
using GRpcStreamingServiceImpl = buga_rpc::DeviceRpcStreaming::Service;

/**
 * This is the gRPC server, which receives calls from the remote client.
 */
class GRemoteProcedureServer : virtual public IRemoteProcedureServer {
public:
    void listen(IRemoteProcedureExecutor &listener, int_between_30000_and_50000 rpcId, bool wait) override;

    void wait() override;

    void stop() override;

    ~GRemoteProcedureServer() override {
        if (shutdownThread.joinable()) {
            shutdownThread.join();
        }
    }

protected:
    std::vector<std::unique_ptr<grpc::Service>> services;
    std::unique_ptr<grpc::Server> server;
    std::thread shutdownThread;
    int_between_30000_and_50000 rpcId = -1;

    void buildAndStart(bool wait);
};

struct GRemoteProcedureStreamingServer : public GRemoteProcedureServer, public IRemoteProcedureStreamingServer {
    void listenStreaming(IRemoteProcedureStreamingExecutor &executor, int_between_30000_and_50000 rpc_id,
                         bool wait) override;
};

// endregion


// region Service

bool handleServerRpc(GRemoteProcedureServer *const parentServer, IRemoteProcedureExecutor &listener, const std::string &name, const Buffer &params, Buffer &ret) {
    if (name == "_rpc_get_version") {
        ret = listener.getVersion();
        return true;
    } else if (name == "_rpc_device_time_usec") {
        ret = std::to_string(std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count());
        return true;
    } else if (name == "_rpc_stop") {
        parentServer->stop();
        return true;
    }
    return false;
}

Status call_impl(GRemoteProcedureServer *const parentServer, IRemoteProcedureExecutor &listener, ServerContext *context, const GRequest *req, GResponse *res) {
    const std::string &name = req->name();
    const Buffer &params = req->buf();

    Buffer ret;
    if (!handleServerRpc(parentServer, listener, name, params, ret)) {
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

/**
 * This is the gRPC "service" implementation (https://grpc.io/img/landing-2.svg), which handles calls on the server.
 * It's a thin translation layer from gRPC "service" to Buga "executor".
 */
class BugaGRpcServiceImpl : virtual public GRpcServiceImpl {
public:
    BugaGRpcServiceImpl(IRemoteProcedureExecutor &listener, GRemoteProcedureServer *parentServer) : listener(listener),
                                                                                                    parentServer(
                                                                                                            parentServer) {}

    Status call(ServerContext *context,
                const GRequest *req,
                GResponse *res) override {
        return call_impl(parentServer, listener, context, req, res);
    }

    Status grpc_echo(ServerContext *context,
                     const GRequest *req,
                     GResponse *res) override;

protected:
    IRemoteProcedureExecutor &listener;
    GRemoteProcedureServer *const parentServer;
};

class BugaGRpcStreamingServiceImpl : public GRpcStreamingServiceImpl {
public:
    BugaGRpcStreamingServiceImpl(IRemoteProcedureStreamingExecutor &listener, GRemoteProcedureServer *parentServer)
            : listener(listener), parentServer(parentServer) {}

    
    Status call(ServerContext *context,
                const GRequest *req,
                GResponse *res) override {
        return call_impl(parentServer, listener, context, req, res);
    }

    Status call_streaming(::grpc::ServerContext *context,
                          ::grpc::ServerReaderWriter<::buga_rpc::GBuffer, ::buga_rpc::GBuffer> *stream) override;

    Status grpc_echo(ServerContext *context, const GRequest *req, GResponse *res) override {
        res->set_buf(req->buf());
        return Status::OK;
    }

protected:
    IRemoteProcedureExecutor &listener;
    GRemoteProcedureServer *const parentServer;
};

struct GRpcBufferStreamWriter : IBufferStreamReaderWriter {
    grpc::ServerReaderWriter<GBuffer, GBuffer> *stream;

    explicit GRpcBufferStreamWriter(grpc::ServerReaderWriter<GBuffer, GBuffer> *stream_) : stream(stream_) {}

    std::unique_ptr<Buffer> read() override {
        GBuffer response;
        std::puts("[GRpcBufferStreamWriter] calling stream->Read");
        if (stream->Read(&response)) {
            std::puts("[GRpcBufferStreamWriter] stream->Read returned true");
            return std::make_unique<Buffer>(response.buf());
        } else {
            std::puts("[GRpcBufferStreamWriter] stream->Read returned false");
            return std::unique_ptr<Buffer>(nullptr);
        }
    }

    bool write(const Buffer &buffer) override {
        GBuffer response;
        response.set_buf(buffer);
        std::puts("[GRpcBufferStreamWriter] calling stream->Write");
        return stream->Write(response);
    }
};

Status BugaGRpcStreamingServiceImpl::call_streaming(::grpc::ServerContext *context,
                                                    ::grpc::ServerReaderWriter<::buga_rpc::GBuffer, ::buga_rpc::GBuffer> *stream) {
    try {
        GBuffer res;

        if (!stream->Read(&res)) {
            return Status(grpc::INVALID_ARGUMENT,
                          "callStreaming must start with procedureName and params sent from client");
        }
        const std::string name = res.buf();

        if (!stream->Read(&res)) {
            return Status(grpc::INVALID_ARGUMENT,
                          "callStreaming must start with procedureName and params sent from client");
        }
        const std::string params = res.buf();

        auto writer = std::make_unique<GRpcBufferStreamWriter>(stream);
        static_cast<IRemoteProcedureStreamingExecutor *>(&this->listener)->executeProcedureStreaming(name, params,
                                                                                                     std::move(writer));
    } catch (RpcError &ex) {
        return Status(grpc::UNKNOWN, std::string("RPC error in executeProcedure: ") + ex.what());
    } catch (std::runtime_error &ex) {
        return Status(grpc::UNKNOWN, std::string("Runtime error in executeProcedure: ") + ex.what());
    } catch (std::exception &ex) {
        return Status(grpc::UNKNOWN, std::string("Exception in executeProcedure: ") + ex.what());
    } catch (...) {
        return Status(grpc::UNKNOWN, std::string("Exception in executeProcedure"));
    }

    return Status::OK;
}

Status BugaGRpcServiceImpl::grpc_echo(ServerContext *context, const GRequest *req, GResponse *res) {
    res->set_buf(req->buf());
    return Status::OK;
}

// endregion


// region Server
void GRemoteProcedureServer::listen(IRemoteProcedureExecutor &listener, int_between_30000_and_50000 rpcId, bool wait) {
    buga_rpc_log("GRemoteProcedureStreamingServer::listen called");
    this->rpcId = rpcId;
    this->services.push_back(std::make_unique<BugaGRpcServiceImpl>(listener, this));
    this->buildAndStart(wait);
}


void GRemoteProcedureStreamingServer::listenStreaming(IRemoteProcedureStreamingExecutor &executor,
                                                      int_between_30000_and_50000 rpc_id, bool wait) {
    buga_rpc_log("GRemoteProcedureStreamingServer::listenStreaming called");
    this->rpcId = rpc_id;
    this->services.push_back(std::make_unique<BugaGRpcStreamingServiceImpl>(executor, this));
    this->buildAndStart(wait);

}

void GRemoteProcedureServer::buildAndStart(bool wait) {
    if (this->services.empty()) {
        throw RpcError("No available services");
    }

    ServerBuilder builder;
    // Listen on the given address without any authentication mechanism.
    std::string server_address = "0.0.0.0:" + std::to_string(this->rpcId);
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    // Register "service" as the instance through which we'll communicate with
    // clients. In this case it corresponds to an *synchronous* service.

    for (auto &service : services) {
        builder.RegisterService(service.get());
    }

    // Set max message size to 1Gb
    const int max_message_size = 1024 * 1024 * 1024;
    builder.SetMaxReceiveMessageSize(max_message_size);
    builder.SetMaxSendMessageSize(max_message_size);
    buga_rpc_log("Server max message size is " + std::to_string(max_message_size) + " bytes");
    // Finally assemble the server.
    this->server = builder.BuildAndStart();
    buga_rpc_log("Server listening on " + server_address);

    if (!this->server)
        throw RpcError("Server object is null (1)");

    if (wait) {
        // Wait for the server to shutdown. Note that some other thread must be
        // responsible for shutting down the server for this call to ever return.
        this->wait();
    }
}

void GRemoteProcedureServer::wait() {
    if (!server)
        throw RpcError("Server object is null (2)");
    server->Wait();
    if (shutdownThread.joinable()) {
        shutdownThread.join();
    }
}

void GRemoteProcedureServer::stop() {
    buga_rpc_log("[GRemoteProcedureServer(" + std::to_string(rpcId) + ")] stop called");
    if (!server)
        throw RpcError("Server object is null (3)");
    shutdownThread = std::thread([&] {
        // The server shouldn't be shutdown from its waiting thread
        server->Shutdown();
    });
}


/**
 * Factory that creates a server instance that uses gRPC for communication.
 */
std::unique_ptr<IRemoteProcedureServer> createBugaGRPCServer() {
    return std::make_unique<GRemoteProcedureServer>();
}


/**
 * Factory that creates a server instance that uses gRPC for communication.
 */
std::unique_ptr<IRemoteProcedureStreamingServer> createBugaGRPCStreamingServer() {
    return std::make_unique<GRemoteProcedureStreamingServer>();
}

// endregion
