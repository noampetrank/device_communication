IFCONFIG_BAD = """rmnet_data1 Link encap:UNSPEC  
          inet addr:10.131.222.118  Mask:255.255.255.252 
          UP RUNNING  MTU:1500  Metric:1
          RX packets:50655 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:41062 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:46081801 TX bytes:7713479 

lo        Link encap:UNSPEC  
          inet addr:127.0.0.1  Mask:255.0.0.0 
          inet6 addr: ::1/128 Scope: Host
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:158 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:158 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1 
          RX bytes:10450 TX bytes:10450 

dummy0    Link encap:UNSPEC  
          inet6 addr: fe80::c055:beff:fe5e:963f/64 Scope: Link
          UP BROADCAST RUNNING NOARP  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:168 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:0 TX bytes:15786 

wlan0     Link encap:UNSPEC    Driver icnss
          UP BROADCAST MULTICAST  MTU:1500  Metric:1
          RX packets:102387 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:59929 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:3000 
          RX bytes:104167017 TX bytes:12027474 

rmnet_data0 Link encap:UNSPEC  
          inet6 addr: fe80::4574:10ba:ad29:1862/64 Scope: Link
          UP RUNNING  MTU:2000  Metric:1
          RX packets:8 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:131 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:620 TX bytes:8305 

rmnet_ipa0 Link encap:UNSPEC  
          UP RUNNING  MTU:2000  Metric:1
          RX packets:21581 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:24491 errors:0 dropped:120 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:46690377 TX bytes:8051328 

p2p0      Link encap:UNSPEC    Driver icnss
          UP BROADCAST MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:3000 
          RX bytes:0 TX bytes:0 
"""
IFCONFIG_GOOD = """lo        Link encap:UNSPEC  
          inet addr:127.0.0.1  Mask:255.0.0.0 
          inet6 addr: ::1/128 Scope: Host
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:158 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:158 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1 
          RX bytes:10450 TX bytes:10450 

dummy0    Link encap:UNSPEC  
          inet6 addr: fe80::c055:beff:fe5e:963f/64 Scope: Link
          UP BROADCAST RUNNING NOARP  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:168 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:0 TX bytes:15786 

wlan0     Link encap:UNSPEC    Driver icnss
          inet addr:10.0.0.101  Bcast:10.0.0.255  Mask:255.255.255.0 
          inet6 addr: fe80::a164:99b5:c01c:ea56/64 Scope: Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:102142 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:59799 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:3000 
          RX bytes:104128278 TX bytes:12007807 

rmnet_data0 Link encap:UNSPEC  
          inet6 addr: fe80::4574:10ba:ad29:1862/64 Scope: Link
          UP RUNNING  MTU:2000  Metric:1
          RX packets:8 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:131 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:620 TX bytes:8305 

rmnet_ipa0 Link encap:UNSPEC  
          UP RUNNING  MTU:2000  Metric:1
          RX packets:21507 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:24382 errors:0 dropped:120 overruns:0 carrier:0 
          collisions:0 txqueuelen:1000 
          RX bytes:46643309 TX bytes:8027566 

p2p0      Link encap:UNSPEC    Driver icnss
          UP BROADCAST MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0 
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0 
          collisions:0 txqueuelen:3000 
          RX bytes:0 TX bytes:0 
"""