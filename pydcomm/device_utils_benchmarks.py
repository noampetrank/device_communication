"""
========================== Format: ==========================
Push file:
                speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total
test_name
push_empty_file         10.0         25.3        208.1    198     0.99      2     0.01     200
push_1kB                12.0         27.3        238.1     98     0.98      2     0.02     100
push_1MB               100.0        250.3       2080.1      7      0.7      3      0.3      10
push_100MB            1000.0       2500.3      20800.1      2     0.67      1     0.33       3
push_1GB                 nan          nan          nan      0      0.0      1      1.0       1



Pull file:
                speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total
test_name
pull_empty_file         10.0         25.3        208.1    198     0.99      2     0.01     200
pull_1kB                12.0         27.3        238.1     98     0.98      2     0.02     100
pull_1MB               100.0        250.3       2080.1      7      0.7      3      0.3      10
pull_100MB            1000.0       2500.3      20800.1      2     0.67      1     0.33       3
pull_1GB                 nan          nan          nan      0      0.0      1      1.0       1



Push+pull file:
                     speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total
test_name
push_pull_empty_file         10.0         25.3        208.1    198     0.99      2     0.01     200
push_pull_1kB                12.0         27.3        238.1     98     0.98      2     0.02     100
push_pull_1MB               100.0        250.3       2080.1      7      0.7      3      0.3      10
push_pull_100MB            1000.0       2500.3      20800.1      2     0.67      1     0.33       3
push_pull_1GB                 nan          nan          nan      0      0.0      1      1.0       1



Set volume:
          speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total
test_name
volume_0          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_1          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_2          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_3          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_4          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_5          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_6          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_7          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_8          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_9          10.0         25.3        208.1    198     0.99      2     0.01     200
volume_10         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_11         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_12         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_13         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_14         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_15         10.0         25.3        208.1    198     0.99      2     0.01     200
volume_16         10.0         25.3        208.1    198     0.99      2     0.01     200



Other DeviceUtils methods:
                      speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total
test_name
send_intent                   10.0         25.3        208.1    198     0.99      2     0.01     200
mkdir                         10.0         25.3        208.1    198     0.99      2     0.01     200
touch_file                    10.0         25.3        208.1    198     0.99      2     0.01     200
ls                            10.0         25.3        208.1    198     0.99      2     0.01     200
get_time                      10.0         25.3        208.1    198     0.99      2     0.01     200
remove                        10.0         25.3        208.1    198     0.99      2     0.01     200
get_device_name               10.0         25.3        208.1    198     0.99      2     0.01     200
get_prop                      10.0         25.3        208.1    198     0.99      2     0.01     200
set_prop                      10.0         25.3        208.1    198     0.99      2     0.01     200
is_earphone_connected         10.0         25.3        208.1    198     0.99      2     0.01     200
is_max_volume                 10.0         25.3        208.1    198     0.99      2     0.01     200




========================== Demo code: ==========================
columns='test_name speed_min_ms speed_avg_ms speed_max_ms n_pass pct_pass n_fail pct_fail n_total'.split()

def table1(name):
    data = []
    data.append((name+'_empty_file 10.0 25.3 208.1 198 0.99 2 0.01 200').split())
    data.append((name+'_1kB 12.0 27.3 238.1 98 0.98 2 0.02 100').split())
    data.append((name+'_1MB 100.0 250.3 2080.1 7 0.7 3 0.3 10').split())
    data.append((name+'_100MB 1000.0 2500.3 20800.1 2 0.67 1 0.33 3').split())
    data.append((name+'_1GB nan nan nan 0 0.0 1 1.0 1').split())
    df = pd.DataFrame(data,columns=columns).set_index(columns[0])
    print(df)

# push
print('Push file:')
table1('push')

# pull
print('\n\n\nPull file:')
table1('pull')

# push+pull
print('\n\n\nPush+pull file:')
table1('push_pull')

# get/set_volume
def append_row(data, name):
    data.append((name+' 10.0 25.3 208.1 198 0.99 2 0.01 200').split())
data = []
for name in ['volume_' + str(x) for x in range(17)]:
    append_row(data, name)
df = pd.DataFrame(data,columns=columns).set_index(columns[0])
print('\n\n\nSet volume:')
print(df)



# the rest (except reboot)
def append_row(data, name):
    data.append((name+' 10.0 25.3 208.1 198 0.99 2 0.01 200').split())
data = []
for name in ('send_intent', 'mkdir', 'touch_file', 'ls', 'get_time', 'remove', 'get_device_name', 'get_prop', 'set_prop', 'is_earphone_connected', 'is_max_volume'):
    append_row(data, name)
df = pd.DataFrame(data,columns=columns).set_index(columns[0])
print('\n\n\nOther DeviceUtils methods:')
print(df)
"""