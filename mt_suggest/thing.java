class MyAudioInterface {  
    public MyAudioInterface() {
        KaddoshCommunicator c = new KaddoshCommunicator((message)-> {
            switch (message.name) {
                case "record_and_play":
                    return doRecordAndPlay(message.song, message.times, message.volume)
                case "somthing_with_result":
                    return getResult(message.p)
            }
        });
    }

    public Promise<RecordAndPlayResult> doRecordAndPlay(byte[] song, int times, int volume) {

    }

    public MyResult(string theParameter) {

    }
}

class Message {
    T getValue<T>(string name);
}

class Result {
    void setValue<T>(string name, T value);
}

interface Receiver {
    Promise<T> handleMessage(Message message)
}

class KaddoshCommunicator {
    public KaddoshCommunicator()
}