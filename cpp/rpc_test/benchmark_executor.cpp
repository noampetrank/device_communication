#include <iostream>
#include "benchmark_executor.h"

Buffer BenchmarkExecutor::executeProcedure(const std::string &procedureName, const Buffer &params) {
    Buffer ret = params;
    for (auto &x : ret) {
        x = (char)((1 + x) % 256);
    }
    return ret;
}

extern "C" std::unique_ptr<IRemoteProcedureExecutor> create_executor() {
    return std::make_unique<BenchmarkExecutor>();
}


class BenchmarkStreamingExecutor : public IRemoteProcedureStreamingExecutor {
public:
    void executeProcedureStreaming(const std::string &procedureName, const Buffer &params,
                                   std::unique_ptr<IBufferStreamReaderWriter> writer) override {
        std::cout << "returning hello world\n";
        writer->write("hello");
        writer->write("world");
    }

    std::string getVersion() override { return "1.0"; }
    Buffer executeProcedure(const std::string &procedureName, const Buffer &params) override {
        return "NOT IMPLEMENTED";
    }
};

extern "C" std::unique_ptr<IRemoteProcedureStreamingExecutor> create_streaming_executor() {
    return std::make_unique<BenchmarkStreamingExecutor>();
}