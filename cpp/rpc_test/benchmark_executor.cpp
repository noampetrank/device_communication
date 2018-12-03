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
