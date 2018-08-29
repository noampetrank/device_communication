using Buffer = std::vector<uint8>;
using MarshalledObject = std::shared_ptr<Buffer>;


template <class T>
MarshalledObject marshall(const T &p);

template <class T>
T unmarshall(const MarshalledObject &buf);


class IRemoteProcedureExecutor {
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) = 0; // Delegate a procedure call from the caller

    virtual void onStart() = 0; // Connection established, do whatever initialization is needed after that.
    virtual void onStop() = 0; // Connection is about to close.

    virtual std::string getVersion() = 0; // Get current executor version
};


class StandardRemoteProcedureExecutor {
    virtual MarshalledObject rpc_echo(std::string procedureName, const MarshalledObject &params) final;
public:
    virtual MarshalledObject delegateProcedure(std::string procedureName, const MarshalledObject &params) final {
        // TODO: move this to .cpp
        if (procedureName == "_rpc_get_version") {
            return marshall(getVersion());
        if (procedureName == "_rpc_echo") {
            return rpc_echo(procedureName, params);
        } else {
            return executeProcedure(procedureName, params);
        }
    }

    virtual void onStart() {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop() {} // Connection is about to close.

    virtual std::string getVersion() { return "1"; }

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledObject onExecuteProcedure(std::string procedureName const MarshalledObject &params) = 0;
};


// Register for intents and pass relevant messages as calls to the listener.
void startListenToAdbIntentProcedureCalls(RemoteProcedureExecutor &listener);







class InputStream {
    int read(MarshalledObject &mo) = 0;  // Returns the amount of objects read (0 or 1), or -1 if the stream has ended/closed.
};

class OutputStream {
    int write(const MarshalledObject &buf) = 0;  // Returns the amount of objects written (0 or 1), or -1 if the stream has ended/closed.
};


// Stream marshaller
MarshalledObject marshall<OutputStream>(OutputStream &p);

// Stream unmarshaller
InputStream unmarshall<InputStream>(const MarshalledObject &buf);



///////
// Stream marshaller C++
class AudioOutputStream : public OutputStream {
    RemoteProcedureExecutor rpc;
public:
    AudioOutputStream(RemoteProcedureExecutor &rpc) : rpc(rpc) {}

    int write(const MarshalledObject &buf) {
        rpc.
    }
};

























