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
INSTANCES_LABEL = "query index"
LABEL_SIZE = 12


class Instance(object):
    pass


instances_per_setting = {}
results_file = "cfinfer_multi.xml"
tree = ET.parse(results_file)
root = tree.getroot()

timeout = float(root.find('pbsjob').get('timeout'))
settings = [ setting.get('name') for setting in root.find('system').findall('setting') ]
for setting in settings:
    instances_per_setting[setting] = []

setting_to_name = {
    'pysdd' : 'pysdd',
    'sharpsat' : 'sharpsat'
}

for spec in root.find('project').findall('runspec'):
    for inst in spec[0]:
        for run in inst:
            instance = Instance()
            instance.time = float(run.find('.//measure[@name="time"]').get('val'))
            instance.exec_times = []
            timed_out = run.find('.//measure[@name="timeout"]').get('val')
            solved = run.find('.//measure[@name="solved"]').get('val')
            if timed_out == 1.0 or solved == 0:
                for i in range(10):
                    value = run.find(f'.//measure[@name="exec_time_{i}"]')
                    if value is not None:
                        instance.exec_times.append(float(value.get('val')))
                    else:
                        instance.exec_times.append(float(timeout))
                        instance.exec_times[i-1] = float(timeout)
            else:
                for i in range(10):
                    value = run.find(f'.//measure[@name="exec_time_{i}"]')
                    if value is not None:
                        instance.exec_times.append(float(value.get('val')))
                    else:
                        instance.exec_times.append(float(timeout))
                        instance.exec_times[i-1] = float(timeout)

            instance.setting = run.find('.//measure[@name="setting"]').get('val')
            instance.name = run.find('.//measure[@name="instance"]').get('val')
            instances_per_setting[instance.setting].append(instance)


fig, axes = plt.subplots(nrows=3, ncols=3)
with open("multi_queries.csv", "r") as queries:
    line_to_query = queries.readlines()[1::10]
    line_to_query = [ query.split(",")[0] for query in line_to_query ]

line_to_nk = []
for query in line_to_query:
    tokens = query.split("_")
    n = int(tokens[1])
    k = int(tokens[2][:-3])
    line_to_nk.append((n,k))

ns = list(set( n for n,k in line_to_nk ))
ns.sort()
ks = list(set( k for n,k in line_to_nk ))
ks.sort()
n_to_idx = { n : i for i,n in enumerate(ns)}
k_to_idx = { k : i for i,k in enumerate(ks)}


fig, axes = plt.subplots(nrows=3, ncols=3)
for instance in instances_per_setting["sharpsat"]:
    line = int(instance.name)
    query = line_to_query[line]
    tokens = query.split("_")
    n = int(tokens[1])
    k = int(tokens[2][:-3])
    data = [ time for time in instance.exec_times if time < float(timeout) - 50 ]
    if len(data) > 0:
        max_time = max(data)
    else:
        max_time = timeout
    axes[n_to_idx[n]][k_to_idx[k]].plot(range(len(data)), data)
    axes[n_to_idx[n]][k_to_idx[k]].set_xlim([0,9])
    axes[n_to_idx[n]][k_to_idx[k]].set_ylim([0,min(max_time*1.2, 3200.0)])
    axes[n_to_idx[n]][k_to_idx[k]].set_ylabel(TIME_LABEL, size = LABEL_SIZE)
    axes[n_to_idx[n]][k_to_idx[k]].set_xlabel(INSTANCES_LABEL, size = LABEL_SIZE)
    axes[n_to_idx[n]][k_to_idx[k]].set_title(f"Width {k}, Size {n}", size = LABEL_SIZE)


fig.tight_layout()
plt.show()


fig, axes = plt.subplots(nrows=3, ncols=3)
for instance in instances_per_setting["pysdd"]:
    line = int(instance.name)
    query = line_to_query[line]
    tokens = query.split("_")
    n = int(tokens[1])
    k = int(tokens[2][:-3])
    data = [ time for time in instance.exec_times if time < float(timeout) - 50 ]
    if len(data) > 0:
        max_time = max(data)
    else:
        max_time = timeout
    axes[n_to_idx[n]][k_to_idx[k]].plot(range(len(data)), data)
    fit = np.polyfit(range(0,len(data)),data[0:],1) # increase order to get better fit
    fitted = [ fit[1] + fit[0]*i for i in range(0, len(data)) ]
    axes[n_to_idx[n]][k_to_idx[k]].plot(range(0,len(data)),fitted)
    axes[n_to_idx[n]][k_to_idx[k]].set_xlim([0,9])
    axes[n_to_idx[n]][k_to_idx[k]].set_ylim([0,min(max_time*1.2, 3200.0)])
    axes[n_to_idx[n]][k_to_idx[k]].set_ylabel(TIME_LABEL, size = LABEL_SIZE)
    axes[n_to_idx[n]][k_to_idx[k]].set_xlabel(INSTANCES_LABEL, size = LABEL_SIZE)
    axes[n_to_idx[n]][k_to_idx[k]].set_title(f"Width {k}, Size {n}", size = LABEL_SIZE)


fig.tight_layout()
plt.show()
