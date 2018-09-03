package com.buga.grpc.cpp;

import android.support.annotation.Keep;

public interface BugaRpcExecutor {
    @Keep
    MarshaledObject executeProcedure(String procedureName, MarshaledObject params);
}
