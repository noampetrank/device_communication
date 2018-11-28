#ifndef GRPC_TEST_BENCHMARK_EXECUTOR_H
#define GRPC_TEST_BENCHMARK_EXECUTOR_H

#include "rpc_bindings/bugarpc.h"

class BenchmarkExecutor : public IRemoteProcedureExecutor {
public:
    Buffer executeProcedure(const std::string &procedureName, const Buffer &params) override;
    std::string getVersion() override { return "1.0"; }
};

#endif //GRPC_TEST_BENCHMARK_EXECUTOR_H
