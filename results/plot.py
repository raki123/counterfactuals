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
    'hard_pysdd' : 'hard_pysdd',
    'hard_sharpsat' : 'hard_sharpsat',
    'easy_pysdd' : 'easy_pysdd',
    'easy_sharpsat' : 'easy_sharpsat',
}

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            instances_per_setting[instance.setting].append(instance)

if False:
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
    plt.legend(loc="upper right", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.show()

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
    plt.legend(loc="upper right", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.show()

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
    plt.legend(loc="upper right", prop={'size': LABEL_SIZE})
    plt.tight_layout()
    plt.show()


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
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
cmap = matplotlib.colormaps.get_cmap("inferno")

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(height + 2, width + 2),
                         gridspec_kw={'width_ratios': [width + 1, 1], 'height_ratios': [1, height + 1], 'wspace': 0.1, 'hspace': 0.1})

extent=[0, width, 0, height]

for i in range(2):
    for j in range(2):
        axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]])
        axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]])

axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect=1/(height + 1), origin='lower')
axes[0][0].set_yticks([])
axes[0][0].xaxis.tick_top()

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect=width, origin='lower')
axes[1][1].set_xticks([])
axes[1][1].yaxis.tick_right()

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect=1, origin='lower')

axes[0][1].axis('off')



fig.tight_layout()

fig.subplots_adjust(right=0.7)
cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
fig.colorbar(im, cax=cbar_ax)
plt.show()

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
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
cmap = matplotlib.colormaps.get_cmap("inferno")

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(height + 2, width + 2),
                         gridspec_kw={'width_ratios': [width + 1, 1], 'height_ratios': [1, height + 1], 'wspace': 0.1, 'hspace': 0.1})

extent=[0, width, 0, height]

for i in range(2):
    for j in range(2):
        axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]])
        axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]])

axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect=1/(height + 1), origin='lower')
axes[0][0].set_yticks([])
axes[0][0].xaxis.tick_top()

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect=width, origin='lower')
axes[1][1].set_xticks([])
axes[1][1].yaxis.tick_right()

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect=1, origin='lower')

axes[0][1].axis('off')



fig.tight_layout()

fig.subplots_adjust(right=0.7)
cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
fig.colorbar(im, cax=cbar_ax)
plt.show()