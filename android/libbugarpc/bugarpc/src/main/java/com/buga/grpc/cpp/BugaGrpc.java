package com.buga.grpc.cpp;

public class BugaGrpc {
    static {
        System.loadLibrary("buga_grpc");
    }

    public native void registerExecutor(BugaRpcExecutor executor);

    public native boolean startServer(int port);

    public native void stopServer();
}
