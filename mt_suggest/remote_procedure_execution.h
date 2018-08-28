typedef Buffer std::vector<uint8>;
struct MarshalledObject {
    std::shared_ptr<Buffer> bytes;
    std::map<std::string, std::string> attachments;
};
typedef std::map<std::string, std::shared_ptr<MarshalledObject>> MarshalledParams;

class RemoteProcedureExecutor {
    const int VERSION = 1;
public:
    MarshalledParams on_procedure_called(std::string procedure_name, const MarshalledParams &params) final {
        if (procedure_name == "_rpc_get_version") {
            MarshalledParams ret = start(params);
            ret['version'] = VERSION;
            return ret;
        } else {
            return execute_procedure(procedure_name, params);
        }
    }

    virtual void start() {} // Do whatever it takes to start listening.
    virtual void stop() {} // Go to bed.

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledParams execute_procedure(std::string procedure_name const MarshalledParams &params) = 0;
};


// Register for intents and pass relevant messages as calls to the listener.
void start_listen_to_adb_intent_procedure_calls(RemoteProcedureExecutor &listener);



//TODO: can marshalling be implemented using our to/from JSON mechanism?

// Marshaller
template <class T>
bool can_marshall(const T &p);

template <class T>
MarshalledObject marshall(const T &p);


// Unmarshaller
template <class T>
bool can_unmarshall(const MarshalledObject &buf);

template <class T>
T unmarshall(const MarshalledObject &buf);




class InputStream {
    int read(MarshalledObject &mo) = 0;  // Returns the amount of objects read (0 or 1), or -1 if the stream has ended/closed.
};

class OutputStream {
    int write(const MarshalledObject &buf) = 0;  // Returns the amount of objects written (0 or 1), or -1 if the stream has ended/closed.
};


// Stream marshaller
bool can_marshall<OutputStream>(const  &p);
MarshalledObject marshall<OutputStream>(const OutputStream &p);

// Stream unmarshaller
bool can_unmarshall<InputStream>(const MarshalledObject &buf);
InputStream unmarshall<InputStream>(const MarshalledObject &buf);
