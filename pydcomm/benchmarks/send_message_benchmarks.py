"""

========================== Format: ==========================
send_message:
                                       total_times success auto_recover manual_recover fail avg_speed_ms max_speed_ms min_speed_ms

send_message_3min_song                         100      90            5              5    0        60000       100000        50000
send_message_1min_song                         300     295            4              1    0        22000        26000        18000
send_message_10sec_song                        500     500            0              0    0         5000        10000         3000
send_message_control_message_0s_sleep        10000   10000            0              0    0           34          100           10
send_message_control_message_5s_sleep         2880    2880            0              0    0           34           70           10
send_message_control_message_60s_sleep         240     240            0              0    0           34           70           10
send_message_receive_3min_song                 100      90            5              5    0        60000       100000        50000
send_message_receive_1min_song                 300     295            4              1    0        22000        26000        18000
send_message_receive_10sec_song                500     500            0              0    0         5000        10000         3000


Fixes:
                      fix_time_sec  mtbf success_rate

fail_error1_autofix              1   120           50
fail_error2_autofix              2   200           50
fail_error3_manualfix           15  1000           80
fail_error4_manualfix           60  2000           90
total_fix_time                  90   120          100

* error<no> will be replaced by fixes that we have implemented.


To calculate the environment effects on a recording script:
No. of recordings * Length of send_message + Fail percent for length * Avg time to fix = Amount of time recordings should take



(Big strings copied from google sheets):

========================== Demo code: ==========================
# (Big strings copied from google sheets):
import pandas as pd

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def pretty_print_tsv(data):
    d = [x.split("\t") for x in data.splitlines()]
    print(pd.DataFrame(d[1:], columns=d[0]).set_index(d[0][0]))


def main():
    times = \"""	total_times	success	auto_recover	manual_recover	fail	avg_speed_ms	max_speed_ms	min_speed_ms
send_message_3min_song	100	90	5	5	0	60000	100000	50000
send_message_1min_song	300	295	4	1	0	22000	26000	18000
send_message_10sec_song	500	500	0	0	0	5000	10000	3000
send_message_control_message_0s_sleep	10000	10000	0	0	0	34	100	10
send_message_control_message_5s_sleep	2880	2880	0	0	0	34	70	10
send_message_control_message_60s_sleep	240	240	0	0	0	34	70	10
send_message_receive_3min_song	100	90	5	5	0	60000	100000	50000
send_message_receive_1min_song	300	295	4	1	0	22000	26000	18000
send_message_receive_10sec_song	500	500	0	0	0	5000	10000	3000\"""
    pretty_print_tsv(times)

    errors = \"""	fix_time_sec	mtbf	success_rate
fail_error1_autofix	1	120	50
fail_error2_autofix	2	200	50
fail_error3_manualfix	15	1000	80
fail_error4_manualfix	60	2000	90\"""
    pretty_print_tsv(errors)


if __name__ == "__main__":
    main()
"""
