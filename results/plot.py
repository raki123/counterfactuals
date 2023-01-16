#!/usr/bin/env python3
from operator import mod
import matplotlib
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from matplotlib.ticker import MaxNLocator
from matplotlib import colors
from matplotlib import gridspec
import matplotlib.ticker as mticker

def MatplotlibClearMemory():
    #usedbackend = matplotlib.get_backend()
    #matplotlib.use('Cairo')
    allfignums = matplotlib.pyplot.get_fignums()
    for i in allfignums:
        fig = matplotlib.pyplot.figure(i)
        fig.clear()
        matplotlib.pyplot.close( fig )
    #matplotlib.use(usedbackend) 


paperheight = 11.7
paperwidth = 8.3
margin = 1.0
golden = (1 + 5 ** 0.5) / 2
fig_width = paperwidth - 2*margin
fig_height = fig_width/golden

#labels
TIME_LABEL = "runtime in seconds"
INSTANCES_LABEL = "number of instances solved"
XWIDTH_LABEL = "X-width"
XDWIDTH_LABEL = "X/D-width"
LABEL_SIZE = 12


class Instance(object):
    pass


instances_per_setting = {}
results_file = "results.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []

setting_to_name = {
    'hard_pysdd' : 'pysdd',
    'hard_sharpsat' : 'sharpsat',
    'easy_pysdd' : 'pysdd',
    'easy_sharpsat' : 'sharpsat',
}

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            instances_per_setting[instance.setting].append(instance)

if True:
    plt.gcf().set_size_inches(fig_width, fig_height)
    max_solved = 0
    for setting in settings:
        if "hard" in setting:
            instances = instances_per_setting[setting]
            x = [float(inst.time) for inst in instances]
            x.sort()
            for i,v in enumerate(x):
                if v >= timeout:
                    if i + 1 > max_solved:
                        max_solved = i + 1
                    break
            plt.plot(range(1, len(instances) + 1), x, label=setting_to_name[setting])


    axes = plt.gca()
    axes.set_xlim([0,max_solved + 20])
    axes.set_ylim([0,timeout])
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylabel(TIME_LABEL, size = LABEL_SIZE)
    plt.xlabel(INSTANCES_LABEL, size = LABEL_SIZE)
    plt.title("Generated Instances", size = LABEL_SIZE)
    plt.legend(loc="best", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.savefig("plots/generated.pdf")
    MatplotlibClearMemory()


    plt.gcf().set_size_inches(fig_width, fig_height)
    max_solved = 0
    for setting in settings:
        if "easy" in setting:
            instances = instances_per_setting[setting]
            x = [float(inst.time) for inst in instances]
            x.sort()
            for i,v in enumerate(x):
                if v >= timeout:
                    if i + 1 > max_solved:
                        max_solved = i + 1
                    break
            plt.plot(range(1, len(instances) + 1), x, label=setting_to_name[setting])


    axes = plt.gca()
    axes.set_xlim([0,max_solved + 20])
    axes.set_ylim([0,timeout])
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylabel(TIME_LABEL, size = LABEL_SIZE)
    plt.xlabel(INSTANCES_LABEL, size = LABEL_SIZE)
    plt.title("Real Graphs", size = LABEL_SIZE)
    plt.legend(loc="best", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.savefig("plots/real.pdf")
    MatplotlibClearMemory()

    plt.gcf().set_size_inches(fig_width, fig_height)
    max_solved = 0
    sharpsat_instances = instances_per_setting["hard_sharpsat"]
    sharpsat_instances += instances_per_setting["easy_sharpsat"]
    x = [float(inst.time) for inst in sharpsat_instances]
    x.sort()
    for i,v in enumerate(x):
        if v >= timeout:
            if i + 1 > max_solved:
                max_solved = i + 1
            break
    plt.plot(range(1, len(sharpsat_instances) + 1), x, label="sharpsat")
    pysdd_instances = instances_per_setting["hard_pysdd"]
    pysdd_instances += instances_per_setting["easy_pysdd"]
    x = [float(inst.time) for inst in pysdd_instances]
    x.sort()
    for i,v in enumerate(x):
        if v >= timeout:
            if i + 1 > max_solved:
                max_solved = i + 1
            break
    plt.plot(range(1, len(pysdd_instances) + 1), x, label="pysdd")

    axes = plt.gca()
    axes.set_xlim([0,max_solved + 20])
    axes.set_ylim([0,timeout])
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.ylabel(TIME_LABEL, size = LABEL_SIZE)
    plt.xlabel(INSTANCES_LABEL, size = LABEL_SIZE)
    plt.title("All Instances", size = LABEL_SIZE)
    plt.legend(loc="best", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.savefig("plots/all.pdf")
    MatplotlibClearMemory()


with open("hard_queries.csv", "r") as queries:
    line_to_query = queries.readlines()[1:]
    line_to_query = [ query.split(",")[0] for query in line_to_query ]
    line_to_nk = []
    for query in line_to_query:
        tokens = query.split("_")
        n = int(tokens[1])
        k = int(tokens[2][:-3])
        line_to_nk.append((n,k))

modval = 3
ns = list(set( n for n,k in line_to_nk ))
ns.sort()
ks = list(set( k for n,k in line_to_nk ))
ks.sort()
n_to_idx = { n : (i//modval) for i,n in enumerate(ns)}
k_to_idx = { k : (i//modval) for i,k in enumerate(ks)}
height = int(np.ceil(len(ks)/modval))
width = int(np.ceil(len(ns)/modval))
data = np.zeros((height, width))
count = np.zeros((height, width))

for instance in instances_per_setting["hard_sharpsat"]:
    line = int(instance.name)
    n, k = line_to_nk[line]
    data[[k_to_idx[k]],n_to_idx[n]] += instance.time
    count[[k_to_idx[k]],n_to_idx[n]] += 1

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("inferno")

base_width = paperwidth - 2*margin
base_height = base_width/(2*width + 3)*(height + 1)

fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(base_width, base_height),
                         gridspec_kw={'width_ratios': [width, 1, width, 1, 1], 'height_ratios': [1, height]})

extent=[0, width, 0, height]

for i in range(2):
    for j in range(4):
        ticks_loc = [ i for i in range(width + 1) ]
        axes[i][j].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]], size = 6)
        ticks_loc = [ i for i in range(height + 1) ]
        axes[i][j].yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]], size = 6)


axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][0].set_yticks([])
axes[0][0].set_xticks([])

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][1].set_xticks([])
axes[1][1].set_yticks([])

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][0].set_ylabel("width", size = LABEL_SIZE)
axes[1][0].set_xlabel("size", size = LABEL_SIZE)

axes[0][1].axis('off')

cbar = fig.colorbar(im, cax=axes[1][4], aspect='auto')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel("runtime in seconds", rotation=270)

data = np.zeros((int(np.ceil(len(ks)/modval)), int(np.ceil(len(ns)/modval))))
count = np.zeros((int(np.ceil(len(ks)/modval)), int(np.ceil(len(ns)/modval))))

for instance in instances_per_setting["hard_pysdd"]:
    line = int(instance.name)
    n, k = line_to_nk[line]
    data[[k_to_idx[k]],n_to_idx[n]] += instance.time
    count[[k_to_idx[k]],n_to_idx[n]] += 1

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("inferno")


axes[0][2].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][2].set_yticks([])
axes[0][2].set_xticks([])

axes[1][3].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][3].set_yticks([])
axes[1][3].set_xticks([])

im = axes[1][2].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][2].set_yticks([])
axes[1][2].set_xlabel("size", size = LABEL_SIZE)

axes[0][3].axis('off')
axes[0][4].axis('off')

plt.tight_layout()
plt.savefig("plots/scaling.pdf")
