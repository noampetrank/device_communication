typedef Buffer std::vector<uint8>;
typedef std::map<std::string, std::shared_ptr<Buffer>> MarshalledParams;

class DeviceProcedureCallee {
public:
    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledParams on_procedure_called(std::string procedure_name, const MarshalledParams &params) = 0;
};


// Register for intents and pass relevant messages as calls to the listener.
void start_listen_to_adb_intent_procedure_calls(DeviceProcedureCallee &listener);



//TODO: can marshalling be implemented using our to/from JSON mechanism?

// Marshaller
template <class T>
bool can_marshall(const T &p);

template <class T>
Buffer marshall(const T &p);


// Unmarshaller
template <class T>
bool can_unmarshall(const Buffer &buf);

template <class T>
T unmarshall(const Buffer &buf);




template <typename T>
class InputStream {
    int read(Buffer &buf) = 0;
    int try_read(Buffer &buf) = 0;
    int write(const Buffer &buf) = 0;
};

template <typename T>
class OutputStream {
    int write(const Buffer &buf) = 0;
};


// Stream marshaller
bool can_marshall<OutputStream>(const  &p);
Buffer marshall<OutputStream>(const OutputStream &p);

// Stream unmarshaller
bool can_unmarshall<InputStream>(const Buffer &buf);
InputStream unmarshall<InputStream>(const Buffer &buf);

