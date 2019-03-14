import json
import numpy as np
import pandas as pd
from collections import OrderedDict


def _setup_pandas():
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 100)


def ux_stats_json_to_pandas(ux_stats_data, verbose=False):
    """
    Parses ux_stats.jsons and returns a pandas DataFrame.
    :param str ux_stats_data: content of ux_stats.jsons file
    :param bool verbose: Print final pandas
    :return pandas.DataFrame:
    """
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
            ("start_time", api_call.get('start_time', None)),
            ("end_time", api_call.get('end_time', None)),
            ("call_time_secs", api_call.get('end_time', None) - api_call.get('start_time', None)),
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
        "start_time": 0,
        "end_time": 0,
        "call_time_secs": 0,
        "manual_actions_count": 0,
        "manual_actions_time": 0,
        "is_exception": False,
        "is_automatic": False,
        "args": "",
        "kwargs": "",
        "ret": "",
    })

    all_calls_table['start_time'] = pd.to_datetime(all_calls_table['start_time'], unit='s')
    all_calls_table['end_time'] = pd.to_datetime(all_calls_table['end_time'], unit='s')
    all_calls_table['day'] = all_calls_table['start_time'].dt.floor('d')

    if verbose:
        _setup_pandas()
        print all_calls_table

    return all_calls_table


def get_ux_stats_summary(all_calls_table, verbose=False):
    """
    Summarizes general UX stats on a per-class/method basis.
    index/groupby - class_name function_name hostname pc_ip pc_wifi device_id device_wifi
    columns - automatic_ratio manual_actions_avg avg_time total_manual_time total_exceptions total

    :param pandas.DataFrame all_calls_table: Output from ux_stats_json_to_pandas()
    :param bool verbose: Print final pandas
    :return:
    """
    idx = "class_name function_name hostname pc_ip pc_wifi device_id device_wifi".split()

    all_calls_table = all_calls_table.set_index(idx).astype({
        "call_time_secs": np.float64,
        "manual_actions_count": np.int32,
        "manual_actions_time": np.float64,
        "is_exception": bool,
        "is_automatic": bool,
    })  # type: pd.DataFrame

    gb = all_calls_table.astype({
        "is_exception": np.float64,
        "is_automatic": np.float64,
    })  # type: pd.DataFrame
    gb = gb.groupby(all_calls_table.index.names)

    summary = gb.agg({
        "call_time_secs": np.mean,
        "manual_actions_count": np.mean,
        "manual_actions_time": np.sum,
        "is_exception": np.sum,
        "is_automatic": np.mean,
    }).join(gb.size().to_frame(name='total'))

    summary = summary.rename(columns={
        "call_time_secs": "avg_time",
        "manual_actions_count": "manual_actions_avg",
        "manual_actions_time": "total_manual_time",
        "is_exception": "total_exceptions",
        "is_automatic": "automatic_ratio",
    })

    if verbose:
        _setup_pandas()
        print summary

    return summary


def get_rpc_audio_interface_stats_summary(all_calls_table, verbose=False):
    """
    Summarizes UX stats for RPC audio interface send/receive.
    index/groupby - day class_name proc_name data_len_bin hostname pc_ip
    columns - call_time_secs MBps

    :param pandas.DataFrame all_calls_table: Output from ux_stats_json_to_pandas()
    :param bool verbose: Print final pandas
    :return:
    """
    def _is_format_supported(x):
        return 'args' in x and isinstance(x['args'], list) and all(isinstance(a, dict) for a in x['args'])

    call_calls = all_calls_table[(all_calls_table['class_name'] == 'GRemoteProcedureClient') & (all_calls_table['function_name'] == 'call')]
    call_calls = call_calls[call_calls.apply(_is_format_supported, axis=1)]

    call_calls['proc_name'] = call_calls.apply(lambda x: eval(x['args'][1]['repr']), axis=1)

    upstream_calls = (call_calls[call_calls['proc_name'].isin(('setup_record_and_play',
                                                               'setup_record_dings',
                                                               'set_signal_to_play',
                                                               'get_recording_start_ts',
                                                               'wait_for_recorded_signal'))]
                      .assign(data_len=lambda df: [((row['args'][2]['len'] if len(row['args']) > 2 else None) or
                                                    row['kwargs'].get('params', {'len': None})['len']) for _, row in df.iterrows()]))

    downstream_calls = (call_calls[call_calls['proc_name'].isin(['get_recorded_data',
                                                                 'get_recorded_signal'])]
                        .assign(data_len=lambda df: [ret['len'] for ret in df.ret]))

    downstream_calls = downstream_calls.assign(data_len=lambda df: [ret['len'] for ret in df.ret])

    data_calls = pd.concat([upstream_calls, downstream_calls], axis=0, sort=True).fillna(-1)

    data_calls['MBps'] = data_calls.apply(lambda x: x['data_len'] / x['call_time_secs'] / 2 ** 20, axis=1)

    bins = np.concatenate([[-float('inf'), -1, 0, 1, 100, 1000], np.arange(1, 120) * 48000 * 12, [float('inf')]])
    data_calls['data_len_bin'] = pd.cut(data_calls['data_len'], bins).rename({'data_len': 'bin'})
    gb = data_calls.assign(total=1).groupby(['day', 'class_name', 'proc_name', 'data_len_bin', 'hostname', 'pc_ip', 'pc_wifi', 'device_id', 'device_wifi'])
    summary = gb.agg(OrderedDict([
        ('call_time_secs', np.mean),
        ('MBps', np.mean),
        ('total', 'count'),
    ]))

    if verbose:
        _setup_pandas()
        print summary
        summary.to_clipboard()

    return summary


def main_debug(which):
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
        all_calls_table = ux_stats_json_to_pandas(ux_stats_data, verbose=True)
        get_ux_stats_summary(all_calls_table, verbose=True)

    inner()


def main(json_files='/home/buga/tmp_dir/ux_stats.jsons', query_to_clipboard=None):
    """
    Run and print all summaries in this files on the given files/directories.
    :param str|list[str] json_files: One or list of us_stats.json files or folders containing such files.
    :return
    """
    import os
    if isinstance(json_files, str):
        json_files = [json_files]

    _json_files = []
    for json_file in json_files:
        if os.path.isdir(json_file):
            _json_files += [os.path.join(json_file, x) for x in os.listdir(json_file)]
        else:
            _json_files += [json_file]
    json_files = _json_files

    ux_stats_data = ""
    for json_file in json_files:
        with open(json_file) as f:
            ux_stats_data += f.read()

    all_calls_table = ux_stats_json_to_pandas(ux_stats_data, verbose=True)
    get_ux_stats_summary(all_calls_table, verbose=True)
    df = get_rpc_audio_interface_stats_summary(all_calls_table, verbose=True)
    if query_to_clipboard:
        df.query(query_to_clipboard).to_clipboard(excel=False)


if __name__ == '__main__':
    # main_debug(which=1)

    import sys
    if len(sys.argv) > 1:
        print(sys.argv)
        query_to_clipboard = sys.argv[2] if len(sys.argv) > 2 else None
        main(sys.argv[1], query_to_clipboard=query_to_clipboard)
    else:
        import datetime
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        main(query_to_clipboard='day=="{}"'.format(today))
