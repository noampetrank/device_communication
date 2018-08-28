typedef Buffer std::vector<uint8>;
struct MarshalledObject {
    std::shared_ptr<Buffer> bytes;
    std::map<std::string, std::string> attachments;
};
typedef std::map<std::string, std::shared_ptr<MarshalledObject>> MarshalledParams;

class RemoteProcedureExecutor {
    const std::string VERSION = "1";
public:
    MarshalledParams onProcedureCalled(std::string procedureName, const MarshalledParams &params) final {
        if (procedureName == "_rpc_get_version") {
            MarshalledParams ret = start(params);
            ret['version'] = VERSION;
            return ret;
        } else {
            return executeProcedure(procedureName, params);
        }
    }

    virtual void onStart() {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop() {} // Connection is about to close.

    virtual std::string getVersion() { return "1"; }

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledParams executeProcedure(std::string procedureName const MarshalledParams &params) = 0;
};


// Register for intents and pass relevant messages as calls to the listener.
void startListenToAdbIntentProcedureCalls(RemoteProcedureExecutor &listener);



//TODO: can marshalling be implemented using our to/from JSON mechanism?

// Marshaller
template <class T>
bool canMarshall(const T &p);

template <class T>
MarshalledObject marshall(const T &p);


// Unmarshaller
template <class T>
bool canUnmarshall(const MarshalledObject &buf);

template <class T>
T unmarshall(const MarshalledObject &buf);




class InputStream {
    int read(MarshalledObject &mo) = 0;  // Returns the amount of objects read (0 or 1), or -1 if the stream has ended/closed.
};

class OutputStream {
    int write(const MarshalledObject &buf) = 0;  // Returns the amount of objects written (0 or 1), or -1 if the stream has ended/closed.
};


// Stream marshaller
bool canMarshall<OutputStream>(const  &p);
MarshalledObject marshall<OutputStream>(const OutputStream &p);

// Stream unmarshaller
bool canUnmarshall<InputStream>(const MarshalledObject &buf);
InputStream unmarshall<InputStream>(const MarshalledObject &buf);
