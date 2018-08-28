typedef Buffer std::vector<uint8>;
typedef std::shared_ptr<Buffer> MarshalledObject;

template <class T>
MarshalledObject marshall(const T &p);

template <class T>
T unmarshall(const MarshalledObject &buf);


class RemoteProcedureExecutor {
public:
    MarshalledParams delegateProcedure(std::string procedureName, const MarshalledParams &params) final {
        if (procedureName == "_rpc_get_version") {
            return marshall(getVersion());
        } else {
            return executeProcedure(procedureName, params);
        }
    }

    virtual void onStart() {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop() {} // Connection is about to close.

    virtual std::string getVersion() { return "1"; }

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledParams onExecuteProcedure(std::string procedureName const MarshalledParams &params) = 0;
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
MarshalledObject marshall<OutputStream>(const OutputStream &p);

// Stream unmarshaller
InputStream unmarshall<InputStream>(const MarshalledObject &buf);
