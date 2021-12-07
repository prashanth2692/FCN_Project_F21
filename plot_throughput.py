'''
Plot queue occupancy over time
'''
from helper import *
import re
from matplotlib.ticker import LinearLocator
from pylab import figure
import pdb
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--files', '-f',
                    help="Throughput timeseries output to one plot",
                    required=True,
                    action="store",
                    nargs='+',
                    dest="files")

parser.add_argument('--legend', '-l',
                    help="Legend to use if there are multiple plots.  File names used as default.",
                    action="store",
                    nargs="+",
                    default=None,
                    dest="legend")

parser.add_argument('--out', '-o',
                    help="Output png file for the plot.",
                    default=None, # Will show the plot
                    dest="out")

parser.add_argument('--labels',
                    help="Labels for x-axis if summarising; defaults to file names",
                    required=False,
                    default=[],
                    nargs="+",
                    dest="labels")

parser.add_argument('--xlimit',
                    help="Upper limit of x axis, data after ignored",
                    type=float,
                    default=50)

parser.add_argument('--every',
                    help="If the plot has a lot of data points, plot one of every EVERY (x,y) point (default 1).",
                    default=1,
                    type=int)

args = parser.parse_args()

if args.legend is None:
    args.legend = []
    for file in args.files:
        args.legend.append(file)


m.rc('figure', figsize=(32, 12))
fig = figure()
ax = fig.add_subplot(111)
time_btwn_flows = 2.0
max_len = 0
for i, f in enumerate(sorted(args.files)):
    # print(f)
    data = read_list(f)
    # print(data[0])
    # throughput = []
    # for d in data:
    #     if 'Mbps' in d[1]:
    #         throughput.append(float(d[1].split('Mbps')[0]))
    #     elif 'Kbps' in d[1]:
    #         throughput.append(float(d[1].split('Kbps')[0])/1000)
    #     else:
    #         throughput.append(float(d[1]))

    # print(throughput)
    # print '---', throughput[0]
    throughput = map(float, col(1, data))
    xaxis = range((max_len - len(throughput)), max_len) #map(float, data) #col(7, data))
    max_len = max(max_len, len(throughput))
    # print(len(xaxis), len(throughput))

    print(max_len, len(throughput))
    throughput = np.array(throughput)
    xaxis = np.array(list(xaxis))

    ax.plot(xaxis, throughput, label=args.legend[i])
    ax.xaxis.set_major_locator(LinearLocator(6))

if args.legend is not None:
	plt.legend()
plt.ylabel("Throughput (Mbits)")
plt.grid(True)
plt.xlabel("Seconds")
plt.tight_layout()

if args.out:
    print('saving to', args.out)
    plt.savefig(args.out)
else:
    plt.show()
