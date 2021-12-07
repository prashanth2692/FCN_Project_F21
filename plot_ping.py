'''
Plot ping RTTs over time
'''
from helper import *
import plot_defaults

from matplotlib.ticker import LinearLocator
from pylab import figure

parser = argparse.ArgumentParser()
parser.add_argument('--files', '-f',
                    help="Ping output files to plot",
                    required=True,
                    action="store",
                    nargs='+')

parser.add_argument('--xlimit',
                    help="Upper limit of x axis, data after ignored",
                    type=float,
                    default=800)

parser.add_argument('--out', '-o',
                    help="Output png file for the plot.",
                    default=None)  # Will show the plot

args = parser.parse_args()

def parse_ping(fname):
    ret = []
    lines = open(fname).readlines()
    num = 0
    for i, line in enumerate(lines):
        if "bytes from" in line:
            # print(line)
            try:
                rtt = line.split(" ")[-2]
                rtt = rtt.split("=")[1]
                rtt = float(rtt) * 1000
                print(rtt)
                ret.append(rtt)
                num += 1
            except:
                print('error')
                break
    
    return ret


m.rc('figure', figsize=(32, 12))
fig = figure()
ax = fig.add_subplot(111)
for i, f in enumerate(args.files):
    print(args.files)
    data = parse_ping(f)
    print("data", data)
    # print('col', col(0, data), '\n')
    xaxis = map(float, range(len(data)))
    rtts = map(float, data)
    xaxis = [x - xaxis[0] for x in xaxis]
    # rtts = [r * 1000 for j, r in enumerate(rtts)
    #         if xaxis[j] <= args.xlimit]
    xaxis = [x for x in xaxis if x <= args.xlimit]
    if "bbr" in args.files[i]:
        name = "bbr"
    else:
        name = "cubic"
    ax.plot(xaxis, rtts, lw=2, label=name)
    plt.legend()
    ax.xaxis.set_major_locator(LinearLocator(5))

plt.ylabel("RTT (ms)")
plt.xlabel("Seconds")
plt.grid(True)
plt.tight_layout()

if args.out:
    plt.savefig(args.out)
else:
    plt.show()
