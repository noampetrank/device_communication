import os
from pydcomm.rpc._remote_procedure_call import StandardRemoteProcedureCaller, UnsupportedExecutorVersion, ExecutorConnectionError

# Kadosh
class AdbIntentsProcedureCaller(StandardRemoteProcedureCaller):
    # This is an example for a specific implementation that uses ADB and intents to pass the calls.
    def __init__(self, device_utils, app_name):
        self.app_name = app_name
        self.device_utils = device_utils

    def start(self):
        # Start app
        self.device_utils.start_app(self.app_name)

        # Check version
        xver = None
        while not xver:
            try:
                xver = self.get_executor_version()
                if xver != '1':
                    raise UnsupportedExecutorVersion()
            except ExecutorConnectionError:
                pass

    def _send_and_wait_for_return(self, procedure_name, marshalled_params):
        if len(marshalled_params) < 2**10:
            # Pass params via intent
            self.device_utils.send_intent(self.app_name + '.' + procedure_name, xtra_data=marshalled_params)
        else:
            # Pass params via file
            tmp_local, tmp_device = '/home/buga/tmp/1.tmp', '/sdcard/tmp/1.tmp'
            with open(tmp_local, 'w') as f:
                f.write(marshalled_params)
            self.device_utils.push(tmp_local, tmp_device)
            os.remove(tmp_local)
            self.device_utils.send_intent(self.app_name + '.' + procedure_name, path=tmp_device)

        # Wait for return (here assumed to be passed via file)
        ret_device, ret_local = '/sdcard/tmp/ret1.tmp', '/home/buga/tmp/ret1.tmp'
        while not self.device_utils.ls(ret_device):
            pass
        self.device_utils.pull(ret_device, ret_local)
        with open(ret_local, 'r') as f:
            ret = f.read()
        os.remove(ret_local)
        return ret


# Noam
class LoopbackAiAppController:
    def __init__(self, device_utils):
        self.rpc = AdbIntentsProcedureCaller(device_utils, "MyLoopbackAi")

    def record_and_play(self, song):
        """
        Plays song and records. Returns recording (loopback + recording).
        """
        ret = self.rpc.call("record_and_play",
                            params=dict(song=song, times=100, volume=2),
                            marshaller=dict_marshaller,
                            unmarshaller=numpy_unmarshaller)
        for block in ret:
            yield block
