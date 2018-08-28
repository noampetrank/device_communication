class Message {
    T getValue<T>(string name);
}
interface MessageHandler {
    object handleMessage(Message message);
}

class DeviceSerializer {
    public string serialize(object x);
}

class DeviceCommunicator {
    public DeviceCommunicator(List<DeviceSerializer> ks, MessageHandler h);
    public start();
    public stop();
}
