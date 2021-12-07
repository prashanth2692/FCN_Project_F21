#!/bin/bash
python flows.py --fig-num 6 --cong bbr --time 10 --bw-net 100 --delay 5 --maxq 1024 --dir part2
tcpdump -r part2/capture.dmp -w part2/flow0.dmp "tcp port 1234"
tcpdump -r part2/capture.dmp -w part2/flow1.dmp "tcp port 1235"
tcpdump -r part2/capture.dmp -w part2/flow2.dmp "tcp port 1236"
tcpdump -r part2/capture.dmp -w part2/flow3.dmp "tcp port 1237"
tcpdump -r part2/capture.dmp -w part2/flow4.dmp "tcp port 1238"
cd part2
echo "processing flows..."
for i in 0 1 2 3 4; do
    captcp throughput -u Mbit --stdio flow$i.dmp > captcp$i.txt
    awk "{print (\$1+$i*2-1)(\",\")(\$2) }" < captcp$i.txt > captcp_csv$i.txt
done
cd ../
python plot_throughput.py --xlimit 50 -f part2/captcp_csv* -o part2/part2.png
