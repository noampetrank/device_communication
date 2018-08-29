#include "remote_procedure_execution.h"

// Noam
class LoopbackAIProcedureExecutor : public StandardRemoteProcedureExecutor {
public:
    virtual void onStart() {} // Connection established, do whatever initialization is needed after that.
    virtual void onStop() {} // Connection is about to close.

    virtual std::string getVersion() { return "0.0"; }

    // Unmarshalls the relevant params, runs the procedure, marshalls the returned params and returns them.
    virtual MarshalledObject onExecuteProcedure(std::string procedureName const MarshalledObject &params) {
        if (procedureName == 'record_and_play') {
            auto p = unmarshall<RecordAndPlayParams>(params);
            play(p.song);
            AudioBuffer rec = record();
            return marshall(rec)
        }
    }
};



// Kadosh
class AdbIntentsTBD {
public:
    virtual void listen(IRemoteProcedureExecutor &listener) {
        registerIntent();
    }
}


void main() {
    //Noam
    LoopbackAIProcedureExecutor exec;
    AdbIntentsTBD tbd();
    tbd.listen(exec);
}
