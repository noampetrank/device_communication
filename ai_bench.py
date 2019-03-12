from pybugarec.audio_interfaces.daemon_rpc_audio_interface import DaemonRpcAudioInterface
from pybuga.projects.operational_data.song_files import read_wavfile
import os

ai=DaemonRpcAudioInterface(device_id="10.0.0.100", do_verify_correct_bugarec_tag=False)
ai.start()

def print_cb(rec_start_ts_usec,fail_reason):
    print("Callback with ts={} and fail_reason={}".format(rec_start_ts_usec,fail_reason))
    
from pybugarecspace.infra.utils import config
song=read_wavfile(os.path.join(config.get_songs_path(), 'Titanium.wav'))

test_sizes = [30] + [15]*3 + [5]*5 + [1]*10
for tst in test_sizes:
    ai.record_and_play(song[:,:tst*48000],[1,2],extra_data=True,callback=print_cb)
#    ai.record_dings(tst)
    

    


execfile('/home/buga/device_communication/pydcomm/public/ux_benchmarks/ux_stats_summary.py')
