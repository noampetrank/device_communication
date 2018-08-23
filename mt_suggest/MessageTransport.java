class MyAudioInterface {  
    public MyAudioInterface() {
        KaddoshCommunicator c = new KaddoshCommunicator((message)-> {
            switch (message.name) {
                case "record_and_play":
                    return doRecordAndPlay(message.get<byte[]>('song'), message.get<string>("times"), message.get<int>("volume"));
                case "play":
                    play(message.get<byte[]>('song'));
                case "record":
                    return record(message.get<int>(numFrames));
                case "record_and_play_streaming":
                    KaddoshStream<byte> songStream = message.getStream<byte>("song")
                    return doRecordAndPlayStreaming(songStream);
                    
            }
        });
    }
    
    public byte[] doRecordAndPlay(byte[] song, int times, int volume) {
        recording = record();
        //...
        return recording
        
    }

    public void play(byte[] song) {
        if (alreadyPlaying) {
            throw Exception("Can't play while playing");
        }
        // do play
    }

    public byte[] record(int numFrames){
        if (alreadyRecording) {
            throw Exception("Can't record while recording");
        }
        // do record
    }

    public KaddoshStream<byte> doRecordAndPlayStreaming(KaddoshStream<byte> song){
        recording = KaddoshStream<byte>();
        audioRecord = AudioRecord();
        mediaTrack = MediaTrack();
        while (mediaTrack.play(song.read())){
            recording.write(audioRecord.record());
        }
        recording.close();
    }
}
/*

Messages in initial KaddoshCommunicator are passed on adb intents as json
{
    "type": "RecordAndPlayMessage",
    "name": "action",
    "params": [
        {
            "name":"sad",
            "type":"int",
            "value":"5"
        },
        {
            "name":"song",
            "type":"stream",
            "value": "/data/local/tmp/hayyyyyyy"
        }
    ]
}
*/

class Message {
    T getValue<T>(string name);
}
interface MessageHandler {
    object handleMessage(Message message);
}

class KaddoshSerializer {
    public string serialize(object x);
}

class KaddoshCommunicator {
    public KaddoshCommunicator(KaddoshSerializer ks, MessageHandler h);
    public start();
    public stop();
}


// SERIALIZATION
// Serialization will probably be done with the Jackson library, as such, we will copy how the jackson library adds serializable types
// For our example, we will need to register the byte[] type to be serialized differently.
// https://www.baeldung.com/jackson-custom-serialization

public class ByteArraySerializer extends StdSerializer<byte[]> {
    public ItemSerializer() {
        this(null);
    }
   
    public ItemSerializer(Class<byte[]> t) {
        super(t);
    }
 
    @Override
    public void serialize(
      byte[] value, JsonGenerator jgen, SerializerProvider provider) 
      throws IOException, JsonProcessingException {
        String filePath = saveToFile(value);
        jgen.writeStartObject();
        jgen.writeNumberField("type", "byte[]");
        jgen.writeStringField("filePath", filePath);
        jgen.writeEndObject();
    }
}

// Inside the Serializer we will register the new ByteArraySerializer
SimpleModule module = new SimpleModule();
module.addSerializer(byte[].class, new ByteArraySerializer());

ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(module);
