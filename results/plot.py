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
results_file = "aspmc_choice_3.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
            instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
            instances_per_setting[instance.setting].append(instance)

results_file = "aspmc_choice_more.xml"
tree = ET.parse(results_file)
root = tree.getroot()

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            try:
                instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
                instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
                instances_per_setting[instance.setting].append(instance)
            except:
                continue

n_modval = 1000
k_modval = 10
height = 25
width = 20
data = np.zeros((height, width))
count = np.zeros((height, width))

for instance in instances_per_setting["aspmc_c_s"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += instance.time
        count[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += 1

data_scatter = [[], [], [], []]

for i in range(height):
    for j in range(width):
        if count[i,j] > 0:
            data_scatter[0].append(i*n_modval)
            data_scatter[1].append(j*k_modval)
            data_scatter[2].append(data[i,j]/count[i,j])
            data_scatter[3].append(10*count[i,j])

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], s=data_scatter[3], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/weighted_scatter.pdf")
MatplotlibClearMemory()

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("winter")

base_width = paperwidth - 2*margin
base_height = base_width/(width + 2)*(height + 1)

fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(base_width, base_height),
                         gridspec_kw={'width_ratios': [width, 1, 1], 'height_ratios': [1, height]})

extent=[0, width, 0, height]

# for i in range(2):
#     for j in range(4):
#         ticks_loc = [ i for i in range(width + 1) ]
#         axes[i][j].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]], size = 6)
#         ticks_loc = [ i for i in range(height + 1) ]
#         axes[i][j].yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]], size = 6)


axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][0].set_yticks([])
axes[0][0].set_xticks([])

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][1].set_xticks([])
axes[1][1].set_yticks([])

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][0].set_ylabel("size", size = LABEL_SIZE)
axes[1][0].set_xlabel("treewidth", size = LABEL_SIZE)

axes[0][1].axis('off')

cbar = fig.colorbar(im, cax=axes[1][2], aspect='auto')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel("runtime in seconds", rotation=270)

plt.tight_layout()
plt.savefig("plots/scaling.pdf")
MatplotlibClearMemory()

data_scatter = [[],[], []]

for instance in instances_per_setting["aspmc_c_s"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data_scatter[0].append(instance.clauses)
        data_scatter[1].append(instance.treewidth)
        data_scatter[2].append(instance.time)

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/scatter.pdf")
MatplotlibClearMemory()

instances_per_setting = {}
results_file = "lp2sat.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []


for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            try:
                instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
                instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
                
                instances_per_setting[instance.setting].append(instance)
            except:
                continue

results_file = "lp2sat_more.xml"
tree = ET.parse(results_file)
root = tree.getroot()

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            try:
                instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
                instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
                instances_per_setting[instance.setting].append(instance)
            except:
                continue

data = np.zeros((height, width))
count = np.zeros((height, width))

for instance in instances_per_setting["lp2lpmc"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += instance.time
        count[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += 1


data_scatter = [[], [], [], []]

for i in range(height):
    for j in range(width):
        if count[i,j] > 0:
            data_scatter[0].append(i*n_modval)
            data_scatter[1].append(j*k_modval)
            data_scatter[2].append(data[i,j]/count[i,j])
            data_scatter[3].append(10*count[i,j])

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], s=data_scatter[3], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/weighted_scatter_lp2lp2.pdf")
MatplotlibClearMemory()

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("winter")

base_width = paperwidth - 2*margin
base_height = base_width/(width + 2)*(height + 1)

fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(base_width, base_height),
                         gridspec_kw={'width_ratios': [width, 1, 1], 'height_ratios': [1, height]})

extent=[0, width, 0, height]

# for i in range(2):
#     for j in range(4):
#         ticks_loc = [ i for i in range(width + 1) ]
#         axes[i][j].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]], size = 6)
#         ticks_loc = [ i for i in range(height + 1) ]
#         axes[i][j].yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]], size = 6)


axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][0].set_yticks([])
axes[0][0].set_xticks([])

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][1].set_xticks([])
axes[1][1].set_yticks([])

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][0].set_ylabel("size", size = LABEL_SIZE)
axes[1][0].set_xlabel("treewidth", size = LABEL_SIZE)

axes[0][1].axis('off')

cbar = fig.colorbar(im, cax=axes[1][2], aspect='auto')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel("runtime in seconds", rotation=270)

plt.tight_layout()
plt.savefig("plots/scaling_lp2lp2.pdf")
MatplotlibClearMemory()

data_scatter = [[],[], []]

for instance in instances_per_setting["lp2lpmc"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data_scatter[0].append(instance.clauses)
        data_scatter[1].append(instance.treewidth)
        data_scatter[2].append(instance.time)

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/scatter_lp2lp2.pdf")
MatplotlibClearMemory()

instances_per_setting = {}
results_file = "problog_stats.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []

name_to_instances = {}

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            if instance.name not in name_to_instances:
                name_to_instances[instance.name] = []
            name_to_instances[instance.name].append(instance)
            try:
                instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
                instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
                instances_per_setting[instance.setting].append(instance)
            except:
                continue

results_file = "problog-stat_more.xml"
tree = ET.parse(results_file)
root = tree.getroot()

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst[:1]:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            if instance.name not in name_to_instances:
                name_to_instances[instance.name] = []
            name_to_instances[instance.name].append(instance)
            try:
                instance.clauses = int(run.find('.//measure[@name="cnf-clauses"]').get('val'))
                instance.treewidth = int(run.find('.//measure[@name="tree_width_cnf"]').get('val'))
                instances_per_setting[instance.setting].append(instance)
            except:
                continue


results_file = "problog_v2_nosdd.xml"
tree = ET.parse(results_file)
root = tree.getroot()

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            for ins in name_to_instances[instance.name]:
                ins.time = instance.time


results_file = "problog_more.xml"
tree = ET.parse(results_file)
root = tree.getroot()

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            if instance.setting == "problog_d":
                instance.name = run.find('.//measure[@name="instance"]').get('val')
                for ins in name_to_instances[instance.name]:
                    ins.time = instance.time
            
            


data = np.zeros((height, width))
count = np.zeros((height, width))

for instance in instances_per_setting["problog-stat"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += instance.time
        count[int(instance.clauses/n_modval),int(instance.treewidth/k_modval)] += 1

data_scatter = [[], [], [], []]

for i in range(height):
    for j in range(width):
        if count[i,j] > 0:
            data_scatter[0].append(i*n_modval)
            data_scatter[1].append(j*k_modval)
            data_scatter[2].append(data[i,j]/count[i,j])
            data_scatter[3].append(10*count[i,j])

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], s=data_scatter[3], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/weighted_scatter_problog.pdf")
MatplotlibClearMemory()

data /= count
data_agg_1 = np.zeros((height, 1))
data_agg_1[:,0] = [ sum(data[i,:]) for i in range(height) ]
data_agg_1 /= width
data_agg_2 = np.zeros((1, width))
data_agg_2[0,:] = [ sum(data[:,i]) for i in range(width) ]
data_agg_2 /= height
cmap = matplotlib.colormaps.get_cmap("winter")

base_width = paperwidth - 2*margin
base_height = base_width/(width + 2)*(height + 1)

fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(base_width, base_height),
                         gridspec_kw={'width_ratios': [width, 1, 1], 'height_ratios': [1, height]})

extent=[0, width, 0, height]

# for i in range(2):
#     for j in range(4):
#         ticks_loc = [ i for i in range(width + 1) ]
#         axes[i][j].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_xticklabels([str(n) for n in ns[::modval] + [2*ns[::modval][-1] - ns[::modval][-2]]], size = 6)
#         ticks_loc = [ i for i in range(height + 1) ]
#         axes[i][j].yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
#         axes[i][j].set_yticklabels([str(k) for k in ks[::modval] + [2*ks[::modval][-1] - ks[::modval][-2]]], size = 6)


axes[0][0].imshow(data_agg_2, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[0][0].set_yticks([])
axes[0][0].set_xticks([])

axes[1][1].imshow(data_agg_1, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][1].set_xticks([])
axes[1][1].set_yticks([])

im = axes[1][0].imshow(data, interpolation='none', cmap=cmap, extent=extent, aspect='auto', origin='lower', vmin = 0, vmax = 1800)
axes[1][0].set_ylabel("size", size = LABEL_SIZE)
axes[1][0].set_xlabel("treewidth", size = LABEL_SIZE)

axes[0][1].axis('off')

cbar = fig.colorbar(im, cax=axes[1][2], aspect='auto')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel("runtime in seconds", rotation=270)

plt.tight_layout()
plt.savefig("plots/scaling_problog.pdf")
MatplotlibClearMemory()

data_scatter = [[],[], []]

for instance in instances_per_setting["problog-stat"]:
    if int(instance.clauses/n_modval) < height and int(instance.treewidth/k_modval) < width and ("smoker" in instance.name or "tree" in instance.name):
        data_scatter[0].append(instance.clauses)
        data_scatter[1].append(instance.treewidth)
        data_scatter[2].append(instance.time)

sc = plt.scatter(data_scatter[1], data_scatter[0], c=data_scatter[2], cmap='winter')
cbar = plt.colorbar(sc)
cbar.set_label("runtime in seconds", rotation=90)
plt.xlabel("treewidth")
plt.ylabel("number of clauses")
ax = plt.gca()
ax.set_ylim([0, n_modval*height])
ax.set_xlim([0, k_modval*width])
plt.tight_layout()
plt.savefig("plots/scatter_problog.pdf")
MatplotlibClearMemory()