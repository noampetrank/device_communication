class MyAudioInterface implements AndroidService{  
    DeviceCommunicator _communicator;

    public MyAudioInterface() {
        List<DeviceSerializer> serializers = loadSerializers();
        _communicator = new DeviceCommunicator((message)-> {
            switch (message.name) {
                case "record_and_play":
                    return doRecordAndPlay(message.<byte[]>get("song"), message.<string>get("times"), message.<int>get("volume"));
                case "play":
                    play(message.<byte[]>get('song'));
                case "record":
                    return record(message.<int>get(numFrames));
                case "record_and_play_streaming":
                    DeviceStream<byte> songStream = message.getStream<byte>("song");
                    return doRecordAndPlayStreaming(songStream);
                    
            }
        }, serializers);
    }

    public override onStart(){
        _communicator.start();
    }
    public override onStop(){
        _communicator.stop();
    }
    
    public byte[] doRecordAndPlay(byte[] song, int times, int volume) {
        recording = record();
        //...
        return recording;
        
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

    public DeviceStream<byte> doRecordAndPlayStreaming(DeviceStream<byte> song){
        recording = DeviceStream<byte>();
        audioRecord = AudioRecord();
        mediaTrack = MediaTrack();
        while (mediaTrack.play(song.read())){
            recording.write(audioRecord.record());
        }
        recording.close();
    }
}
/*

Messages in initial DeviceCommunicator are passed on adb intents as json
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

abstract class BugatoneDeviceSerializer<T>{
    public Dictionary<string,string> serialize(T value);
    public bool canDeserializer(json whatever);
    public T deserialize(json);
}

// Inside the Serializer we will register the new ByteArraySerializer
SimpleModule module = new SimpleModule();
module.addSerializer(byte[].class, new ByteArraySerializer());

ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(module);
