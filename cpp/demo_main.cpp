/*
 * This is a toy example that runs a gRPC server on a thread, waits a bit and then makes a few RPC calls to it
 * from a client on another thread.
 * This could be used as an example to creating a C++ gRPC server.
 */

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


//int main(int argc, char **argv) {
//    RunServer();
//    return 0;
//}


// Below this line is code that creates a client as well, and then sends some requests to the server.

#include <iostream>
#include <memory>
#include <string>
#include <thread>

#include <grpcpp/grpcpp.h>

#include "buga_rpc.grpc.pb.h"
#include "buga_rpc.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using buga_rpc::GRequest;
using buga_rpc::GResponse;
using buga_rpc::DeviceRpc;


class BugaClient {
public:
    BugaClient(std::shared_ptr<Channel> channel)
            : stub_(DeviceRpc::NewStub(channel)) {}

    // Assembles the client's payload, sends it and presents the response back
    // from the server.
    std::string getBugaVersion() {
        // Data we are sending to the server.
        GRequest request;
        request.set_name("_rpc_get_version");

        // Container for the data we expect from the server.
        GResponse reply;

        // Context for the client. It could be used to convey extra information to
        // the server and/or tweak certain RPC behaviors.
        ClientContext context;

        // The actual RPC.
        Status status = stub_->call(&context, request, &reply);

        // Act upon its status.
        if (status.ok()) {
            return reply.buf();
        } else {
            std::cout << status.error_code() << ": " << status.error_message()
                      << std::endl;
            return "RPC failed";
        }
    }

    std::string callBugaRpcEcho() {
        // Data we are sending to the server.
        GRequest request;
        request.set_name("_rpc_echo");
        request.set_buf("Buga RPC echo success!!!");

        // Container for the data we expect from the server.
        GResponse reply;

        // Context for the client. It could be used to convey extra information to
        // the server and/or tweak certain RPC behaviors.
        ClientContext context;

        // The actual RPC.
        Status status = stub_->call(&context, request, &reply);

        // Act upon its status.
        if (status.ok()) {
            return reply.buf();
        } else {
            std::cout << status.error_code() << ": " << status.error_message()
                      << std::endl;
            return "RPC failed";
        }
    }

    std::string callGRpcEcho() {
        // Data we are sending to the server.
        GRequest request;
        request.set_buf("gRPC echo success!!!");

        // Container for the data we expect from the server.
        GResponse reply;

        // Context for the client. It could be used to convey extra information to
        // the server and/or tweak certain RPC behaviors.
        ClientContext context;

        // The actual RPC.
        Status status = stub_->grpc_echo(&context, request, &reply);

        // Act upon its status.
        if (status.ok()) {
            return reply.buf();
        } else {
            std::cout << status.error_code() << ": " << status.error_message()
                      << std::endl;
            return "RPC failed";
        }
    }

private:
    std::unique_ptr<DeviceRpc::Stub> stub_;
};



void RunClient() {
    // Instantiate the client. It requires a channel, out of which the actual RPCs
    // are created. This channel models a connection to an endpoint (in this case,
    // localhost at port 50051). We indicate that the channel isn't authenticated
    // (use of InsecureChannelCredentials()).
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    BugaClient bugaClientt(grpc::CreateChannel(
            "localhost:50051", grpc::InsecureChannelCredentials()));
    std::string reply = bugaClientt.callGRpcEcho();
    std::cout << "Server replied: " << reply << std::endl;
    reply = bugaClientt.callBugaRpcEcho();
    std::cout << "Server replied: " << reply << std::endl;
    reply = bugaClientt.getBugaVersion();
    std::cout << "Server version: " << reply << std::endl;
}

int main(int argc, char** argv) {
    std::thread serverThread(RunClient);
    RunServer();
    return 0;
}
