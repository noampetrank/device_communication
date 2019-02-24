import json
import numpy as np
import pandas as pd


def ux_stats_json_to_pandas(ux_stats_data):
    """
    :param str ux_stats_data:
    :return:
    """
    from collections import OrderedDict

    ux_stats_jsons = map(json.loads, ux_stats_data.splitlines())

    def single_api_call_summary(api_call):
        extra_stats = api_call.get('extra_stats', {})
        if extra_stats is None:
            extra_stats = {}

        res = OrderedDict([
            ("class_name", api_call.get('class_name', None)),
            ("function_name", api_call.get('function_name', None)),
            ("hostname", extra_stats.get('hostname', None)),
            ("pc_ip", extra_stats.get('pc_ip', None)),
            ("pc_wifi", extra_stats.get('pc_wifi', None)),
            ("device_id", extra_stats.get('device_id', None)),
            ("device_wifi", extra_stats.get('device_wifi', None)),
            ("call_time", api_call.get('end_time', None) - api_call.get('start_time', None)),
            ("manual_actions_count", len(api_call.get('manual_times', None))),
            ("manual_actions_time", sum([end - start for start, end in api_call.get('manual_times', [])])),
            ("is_exception", api_call.get('is_exception', None)),
            ("is_automatic", len(api_call.get('manual_times', None)) == 0),
            ("args", api_call.get('args', None)),
            ("kwargs", api_call.get('kwargs', None)),
            ("ret", api_call.get('ret', None)),
        ])

        return res

    ux_stats_rows = map(single_api_call_summary, ux_stats_jsons)

    all_calls_table = pd.DataFrame(data=ux_stats_rows).fillna(value={
        "class_name": "N/A",
        "function_name": "N/A",
        "hostname": "N/A",
        "pc_ip": "N/A",
        "pc_wifi": "N/A",
        "device_id": "N/A",
        "device_wifi": "N/A",
        "call_time": 0,
        "manual_actions_count": 0,
        "manual_actions_time": 0,
        "is_exception": False,
        "is_automatic": False,
        "args": "",
        "kwargs": "",
        "ret": "",
    })

    return all_calls_table


def get_ux_stats_summary(all_calls_table, verbose=False):
    """
    :param ps.DataFrame all_calls_table:
    :param bool verbose:
    :return:
    """
    idx = "class_name function_name hostname pc_ip pc_wifi device_id device_wifi".split()

    all_calls_table = all_calls_table.set_index(idx).astype({
        "call_time": np.float64,
        "manual_actions_count": np.int32,
        "manual_actions_time": np.float64,
        "is_exception": bool,
        "is_automatic": bool,
    })

    gb = all_calls_table.astype({
        "is_exception": np.float64,
        "is_automatic": np.float64,
    }).groupby(all_calls_table.index.names)

    summary = gb.agg({
        "call_time": np.mean,
        "manual_actions_count": np.mean,
        "manual_actions_time": np.sum,
        "is_exception": np.sum,
        "is_automatic": np.mean,
    }).join(gb.size().to_frame(name='total'))

    summary = summary.rename(columns={
        "call_time": "avg_time",
        "manual_actions_count": "manual_actions_avg",
        "manual_actions_time": "total_manual_time",
        "is_exception": "total_exceptions",
        "is_automatic": "automatic_ratio",
    })

    if verbose:
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)
        print all_calls_table
        print summary

    return all_calls_table, summary


def main_test(which):
    from mock import patch

    @patch('pydcomm.public.ux_stats.ApiCallsRecorder._get_save_file')
    def inner(mock_get_save_file):
        import os
        from pydcomm.public.ux_stats import ApiCallsRecorder, metacollectstats
        from pydcomm.public.ux_benchmarks.common_extra_stats import CommonExtraStats

        alt_json_file = "/home/buga/tmp_dir/ux_stats.tmp.jsons"
        try:
            os.remove(alt_json_file)
        except OSError:
            pass

        mock_get_save_file.side_effect = lambda: open(alt_json_file, "a")
        # ApiCallsRecorder._get_save_file = _get_save_file
        recorder = ApiCallsRecorder()

        with recorder:
            if which == 1:
                class Dummy(CommonExtraStats):
                    __metaclass__ = metacollectstats

                    def __init__(self, ip_port):
                        pass

                    def __extra_stats__(self):
                        common = super(Dummy, self).__extra_stats__()
                        common.update({
                            "device_id": "8.7.6.5",
                        })
                        return common

                    @classmethod
                    def create_connection(cls, rpc_id, device_id=None):
                        pass

                    def call(self, procedure_name, params):
                        pass

                Dummy.create_connection(1234, "1.2.3.4")
                dummy = Dummy("1.2.3.4:5555")
                dummy.call("echo", "4321")
                dummy.call("echo", "543")

            elif which == 2:
                from pybugarec.audio_interfaces.daemon_rpc_audio_interface import DaemonRpcAudioInterface
                ai = DaemonRpcAudioInterface(device_id="10.0.0.129", do_verify_correct_bugarec_tag=False)
                ai.start()

        with open(alt_json_file) as f:
            ux_stats_data = f.read()
        all_calls_table = ux_stats_json_to_pandas(ux_stats_data)
        get_ux_stats_summary(all_calls_table, True)

    inner()


def main(json_files):
    import os
    if isinstance(json_files, str):
        if os.path.isdir(json_files):
            json_files = os.listdir(json_files)
        else:
            json_files = [json_files]

    ux_stats_data = ""
    for json_file in json_files:
        with open(json_file) as f:
            ux_stats_data += f.read()

    all_calls_table = ux_stats_json_to_pandas(ux_stats_data)
    get_ux_stats_summary(all_calls_table, True)


if __name__ == '__main__':
    main_test(which=1)

    # import sys
    # main(sys.argv[1]) #TODO