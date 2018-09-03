using Buffer = std::vector<uint8>;
using MarshalledObject = std::shared_ptr<Buffer>;

template <class T>
MarshalledObject marshall(const T &p);

template <class T>
T unmarshall(const MarshalledObject &buf);


class IRemoteProcedureExecutor {
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) = 0; // Delegate a procedure call from the caller
    virtual std::string getVersion() = 0; // Get current executor version
    virtual ~IRemoteProcedureExecutor() = default;
};


class StandardRemoteProcedureExecutor {
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) final override {
        // TODO: move this to .cpp
        if (procedureName == "_rpc_get_version") {
            return marshall(getVersion());
        } if (procedureName == "_rpc_echo") {
            return rpc_echo(params);
        } if (procedureName == "_rpc_start") {
            return onStart(params);
        } if (procedureName == "_rpc_stop") {
            return onStop(params);
        } else {
            return executeProcedure(procedureName, params);
        }
    }

    virtual std::string getVersion() { return "0.0"; }

protected:
    virtual void onStart() {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop() {} // Connection is about to close.

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledObject onExecuteProcedure(std::string procedureName const MarshalledObject &params) = 0;

private:
    virtual MarshalledObject rpc_echo(const MarshalledObject &params) final;
};


class IRemoteProcedureServer {
public:
    // Listens; calls delegate when stuff arrives
    virtual void listen(IRemoteProcedureExecutor &listener) = 0;
    virtual ~IRemoteProcedureServer() = default;
}



// TODO add streaming API

