#!/bin/bash
python flows.py --fig-num 7 --cong bbr --time 100 --bw-net 10 --delay 10 --maxq 200 --dir bonus
tcpdump -r bonus/h1_capture.dmp -w bonus/flow1.dmp "tcp port 1235"
tcpdump -r bonus/h1_capture.dmp -w bonus/flow0.dmp "tcp port 1234"
cd bonus

for i in 0 1; do
    captcp throughput -u Mbit -f 2 --stdio flow$i.dmp > captcp$i.txt
    awk '{print $1","$2 }' < captcp$i.txt > captcp-csv$i.txt
done
cd ../
python plot_throughput.py --xlimit 100 -f bonus/captcp-csv* -o bonus/bonus.png -l cubic bbr
