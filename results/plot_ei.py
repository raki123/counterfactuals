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

paperheight = 11.7
paperwidth = 8.3
margin = 1.0

#labels
TIME_LABEL = "runtime in seconds"
INSTANCES_LABEL = "number of instances solved"
LABEL_SIZE = 12


class Instance(object):
    pass


instances_per_setting = {}
results_file = "cfinfer_ei.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []

setting_to_name = {
    'pysdd' : 'pysdd',
    'sharpsat' : 'sharpsat',
}

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            instances_per_setting[instance.setting].append(instance)

with open("ei_queries.csv", "r") as queries:
    line_to_query = queries.readlines()[1:]
    line_to_query = [ query.split(",") for query in line_to_query ]
    line_to_ei = []
    for query in line_to_query:
        e = len(query[2].split(";")) - 1
        if query[2].startswith("\\+reach(116);\\+"):
            e = -e
        if len(query[3]) == 1:
            i = 0
        else:
            i = len(query[3].split(";"))
            if query[3].startswith("\\+"):
                i = -i
        line_to_ei.append((e,i))

modval = 1
es = list(set( n for n,k in line_to_ei ))
es.sort()
Is = list(set( k for n,k in line_to_ei ))
Is.sort()
e_to_idx = { n : (i//modval) for i,n in enumerate(es)}
i_to_idx = { k : (i//modval) for i,k in enumerate(Is)}
height = int(np.ceil(len(Is)/modval))
width = int(np.ceil(len(es)/modval))
data = np.zeros((height, width))
count = np.zeros((height, width))

for instance in instances_per_setting["sharpsat"]:
    line = int(instance.name)
    e, i = line_to_ei[line]
    data[i_to_idx[i],e_to_idx[e]] += instance.time
    count[i_to_idx[i],e_to_idx[e]] += 1

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("winter")

base_width = paperwidth - 2*margin
base_height = base_width/(2*width + 3)*(height + 1)

fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(base_width, base_height),
                         gridspec_kw={'width_ratios': [width, 1, width, 1, 1], 'height_ratios': [1, height]})

extent=[0, width, 0, height]

for i in range(2):
    for j in range(4):
        ticks_loc = [ i + 0.5 for i in range(width) ]
        axes[i][j].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        axes[i][j].set_xticklabels([str(n) for n in es[::modval]], size = 6)
        ticks_loc = [ i + 0.5 for i in range(height) ]
        axes[i][j].yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        axes[i][j].set_yticklabels([str(k) for k in Is[::modval]], size = 6)

axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][0].set_yticks([])
axes[0][0].set_xticks([])

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][1].set_xticks([])
axes[1][1].set_yticks([])

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][0].set_ylabel("interventions", size = LABEL_SIZE)
axes[1][0].set_xlabel("evidence", size = LABEL_SIZE)

axes[0][1].axis('off')

cbar = fig.colorbar(im, cax=axes[1][4], aspect='auto')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel("runtime in seconds", rotation=270)

data = np.zeros((int(np.ceil(len(Is)/modval)), int(np.ceil(len(es)/modval))))
count = np.zeros((int(np.ceil(len(Is)/modval)), int(np.ceil(len(es)/modval))))

for instance in instances_per_setting["pysdd"]:
    line = int(instance.name)
    e, i = line_to_ei[line]
    data[i_to_idx[i],e_to_idx[e]] += instance.time
    count[i_to_idx[i],e_to_idx[e]] += 1

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("winter")

axes[0][2].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][2].set_yticks([])
axes[0][2].set_xticks([])

axes[1][3].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][3].set_yticks([])
axes[1][3].set_xticks([])

im = axes[1][2].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][2].set_yticks([])
# axes[1][2].set_ylabel("interventions", size = LABEL_SIZE)
axes[1][2].set_xlabel("evidence", size = LABEL_SIZE)

axes[0][3].axis('off')
axes[0][4].axis('off')

plt.tight_layout()
plt.savefig("plots/EI.pdf")