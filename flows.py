#!/usr/bin/python

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.util import dumpNodeConnections

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import os
import sched

parser = ArgumentParser(description="Reproducing BBR reults")

parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="bbr")

parser.add_argument('--fig-num',
                    type=int,
                    help="Figure to replicate. Valid options are 5 or 6",
                    default=6)

parser.add_argument('--no-capture',
                    action='store_true',
                    default=False)

flow_type = 'iperf'
# Expt parameters
args = parser.parse_args()

def capture_packets(options="", fname='./capture.dmp', runner=None):
    cmd = "tcpdump -w {} {}".format(fname, options)
    runner = Popen if runner is None else runner
    return runner(cmd, shell=True).wait()



class BBTopo(Topo):
    "Simple topology for bbr experiments."

    def build(self, n=2):
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        switch = self.addSwitch('s0')
        self.addLink(host1, switch,
                             bw=args.bw_host)
        self.addLink(host2, switch, bw=args.bw_net,
                             delay=str(args.delay) + 'ms',
                             max_queue_size=args.maxq)
        return


def build_topology():
    def runner(popen, noproc=False):
        def run_fn(command, background=False, daemon=True):
            if noproc:
                p = popen(command, shell=True)
                if not background:
                    return p.wait()
            def start_command():
                popen(command, shell=True).wait()
            proc = Process(target=start_command)
            proc.daemon = daemon
            proc.start()
            if not background:
                proc.join()
            return proc
        return run_fn

    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    dumpNodeConnections(net.hosts)
    net.pingAll()
    data = {
        'type': 'mininet',
        'h1': {
            'IP': net.get('h1').IP(),
            'popen': net.get('h1').popen,
        },
        'h2': {
            'IP': net.get('h2').IP(),
            'popen': net.get('h2').popen
        },
        'obj': net,
        'cleanupfn': net.stop
    }
    # disable gso, tso, gro
    h2run = runner(data['h2']['popen'], noproc=False)
    h1run = runner(data['h1']['popen'], noproc=False)
    h1run(
        "sudo ethtool -K h1-eth0 gso off tso off gro off;"
    )
    h2run(
        "sudo ethtool -K h2-eth0 gso off tso off gro off;"
    )

    data['h1']['runner'] = runner(data['h1']['popen'], noproc=False)
    data['h2']['runner'] = runner(data['h2']['popen'], noproc=False)

    return data

def start_capture(outfile="capture.dmp"):
    monitor = Process(target=capture_packets,
                      args=("", outfile))
    monitor.start()
    return monitor


def filter_capture(filt, infile="capture.dmp", outfile="filtered.dmp"):
    monitor = Process(target=capture_packets,
                      args=("-r {} {}".format(infile, filt), outfile))
    monitor.start()
    return monitor

def iperf_setup(h1, h2, ports):
    h2['runner']("killall iperf3")
    sleep(1) # make sure ports can be reused
    for port in ports:
        # -s: server
        # -p [port]: port
        # -f m: format in megabits
        # -i 1: measure every second
        # -1: one-off (one connection then exit)
        cmd = "iperf3 -s -p {} -f m -i 1 -1".format(port)
        h2['runner'](cmd, background=True)
    sleep(min(10, len(ports))) # make sure all the servers start

def iperf_commands(index, h1, h2, port, cong, duration, outdir, delay=0):
    # -c [ip]: remote host
    # -w [size]: TCP buffer size
    # -C: congestion control
    # -t [seconds]: duration
    # -p [port]: port
    # -f m: format in megabits
    # -i 1: measure every second
    window = '-w 16m' if args.fig_num == 6 else ''
    client = "iperf3 -c {} -f m -i 1 -p {} {} -C {} -t {} > {}".format(
        h2['IP'], port, window, cong, duration, "{}/iperf{}.txt".format(outdir, index)
    )
    h1['runner'](client, background=True)

def start_flows(net, num_flows, time_btwn_flows, cong):
    h1 = net['h1']
    h2 = net['h2']

    flows = []
    base_port = 1234

    iperf_setup(h1, h2, [base_port + i for i in range(num_flows)])

    def start_flow(i):
        iperf_commands(i, h1, h2, base_port + i, cong[i],
                      args.time - time_btwn_flows * i,
                      args.dir, delay=i*time_btwn_flows)
        flow = {
            'index': i,
            'send_filter': 'src {} and dst {} and dst port {}'.format(h1['IP'], h2['IP'],
                                                                      base_port + i),
            'receive_filter': 'src {} and dst {} and src port {}'.format(h2['IP'], h1['IP'],
                                                                         base_port + i),
            'monitor': None
        }
        flow['filter'] = '"({}) or ({})"'.format(flow['send_filter'], flow['receive_filter'])
        flows.append(flow)
    
    s = sched.scheduler(time, sleep)
    for i in range(num_flows):
        s.enter(i * time_btwn_flows, 1, start_flow, [i])
    
    s.run()
    
    return flows

# Start a ping train between h1 and h2 lasting for the given time. Send the
# output to the given fname.
def start_ping(net, time, fname):
    h1 = net['h1']
    h2 = net['h2']
    command = "ping -i 0.1 -c {} {} > {}/{}".format(
        time*10, h2['IP'],
        args.dir, fname
    )
    h1['runner'](command, background=True)

def run(action):
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    net = build_topology()
    if action:
        action(net)

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net['obj'])

    if net['obj'] is not None and net['cleanupfn']:
        net['cleanupfn']()

# Display a countdown to the user to show time remaining.
def display_countdown(nseconds):
    start_time = time()
    while True:
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > nseconds:
            break
        print("%.1fs left..." % (nseconds - delta))

def figure5(net):
    if not args.no_capture:
        cap = start_capture("{}/capture_bbr.dmp".format(args.dir))

    flows = start_flows(net, 1, 0, ["bbr"])
    display_countdown(args.time + 5)

    if not args.no_capture:
        Popen("killall tcpdump", shell=True)
        cap.join()
        filter_capture(flows[0]['filter'],
                       "{}/capture_bbr.dmp".format(args.dir),
                       "{}/flow_bbr.dmp".format(args.dir))
        cap = start_capture("{}/capture_cubic.dmp".format(args.dir))

    flows = start_flows(net, 1, 0, ["cubic"])
    display_countdown(args.time + 5)

    if not args.no_capture:
        Popen("killall tcpdump", shell=True)
        cap.join()
        filter_capture(flows[0]['filter'],
                       "{}/capture_cubic.dmp".format(args.dir),
                       "{}/flow_cubic.dmp".format(args.dir))

def figure6(net):
    """ """
    # Start packet capturing
    if not args.no_capture:
        cap = start_capture("{}/capture.dmp".format(args.dir))

    # Start the iperf flows.
    n_iperf_flows = 5
    time_btwn_flows = 2
    cong = [args.cong for x in range(n_iperf_flows)]
    flows = start_flows(net, n_iperf_flows, time_btwn_flows, cong)

    # print(time left to show user how long they have to wait.)
    display_countdown(args.time + 15)

    if not args.no_capture:
        Popen("killall tcpdump", shell=True)
        cap.join()

    for flow in flows:
        if flow['filter'] and not args.no_capture:
            print("Filtering flow {}...".format(flow['index']))
            filter_capture(flow['filter'],
                           "{}/capture.dmp".format(args.dir),
                           "{}/flow{}.dmp".format(args.dir, flow['index'])) 
        if flow['monitor'] is not None:
            flow['monitor'].terminate()

def bonus(net):
    """ """
    # Start packet capturing
    if not args.no_capture:
        cap = start_capture("{}/capture.dmp".format(args.dir))

    # Start the iperf flows.
    flows = start_flows(net, 2, 0, ["cubic", "bbr"])

    # print(time left to show user how long they have to wait.)
    display_countdown(args.time + 5)

    if not args.no_capture:
        Popen("killall tcpdump", shell=True)
        cap.join()

    for flow in flows:
        if flow['filter'] and not args.no_capture:
            print("Filtering flow {}...".format(flow['index']))
            filter_capture(flow['filter'],
                           "{}/capture.dmp".format(args.dir),
                           "{}/flow{}.dmp".format(args.dir, flow['index'])) 
        if flow['monitor'] is not None:
            flow['monitor'].terminate()

if __name__ == "__main__":
    if args.fig_num == 5:
        run(figure5)
    elif args.fig_num == 6:
        run(figure6)
    elif args.fig_num == 7:
        run(bonus)
    else:
        print("Error: please enter a valid figure number: 5 or 6 or 7")