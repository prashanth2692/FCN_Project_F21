This project consists of 3 experiments

Dependencies:
1) mininet 
2) python
3) tcpdump
4) captcp
5) iperf3
6) python packages
    a) matplotlib
    b) mininet

Experiment 1: RTT comparision between Cubic and BBR

Instructions to run the experiments.
```
python flows.py --fig-num 5 --time 8 --bw-net 10 --delay 20 --maxq 175 --dir part1

tcpdump -r part1/capture_cubic.dmp -w part1/flow_cubic.dmp "(src 10.0.0.1 and dst 10.0.0.2 and dst port 1234) or (src 10.0.0.2 and dst 10.0.0.1 and src port 1234)"

tcpdump -r part1/capture_bbr.dmp -w part1/flow_bbr.dmp "tcp port 22"

su $SUDO_USER -c "tshark -2 -r part1/flow_bbr.dmp -R 'tcp.stream eq 1 && tcp.analysis.ack_rtt'  -e frame.time_relative -e tcp.analysis.ack_rtt -Tfields -E separator=, > part1/bbr_rtt2.txt"

su $SUDO_USER -c "tshark -2 -r part1/flow_cubic.dmp -R 'tcp.stream eq 1 && tcp.analysis.ack_rtt'  -e frame.time_relative -e tcp.analysis.ack_rtt -Tfields -E separator=, > part1/cubic_rtt2.txt"

python plot_ping.py -f part1/bbr_rtt2.txt part1/cubic_rtt2.txt --xlimit 8 -o part1/part1.png
```

Experiment 2: Fairness between BBR flows.
```
sudo bash ./part2.sh
```

Experiment 3: BBR Vs Cubic (Bonus).
```
sudo bash ./part3.sh
```
