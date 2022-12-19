import sys
import networkx as nx
import random
import csv
from aspmc.graph.treedecomposition import from_graph

with open(f"chosen/{sys.argv[1]}", 'r') as in_file:
    graph = nx.Graph()
    for line in in_file:
        line.strip()
        if line.startswith("%"):
            continue
        if len(line) == 0:
            continue
        if not line.startswith("edge"):
            print(line)
        line = line[5:-3]
        v, w = line.split(",")
        graph.add_edge(v,w)
    comps = list(nx.connected_components(graph))
    if len(comps) > 1:
        graph = graph.subgraph(comps[0])

    td = from_graph(graph)
    if td.width < 10:
        print("easy")
        exit(0)

    periphery = nx.periphery(graph)
    node = periphery[0]
    digraph = nx.DiGraph()
    digraph.add_edges_from((u,v) for (u,v) in nx.traversal.bfs_edges(graph, node) if u != v)
    ts = list(nx.topological_sort(digraph))
    v_to_i = { v : i for i, v in enumerate(ts) }
    network = nx.DiGraph() 
    network.add_edges_from( (u,v) if v_to_i[v] > v_to_i[u] else (v,u) for u,v in graph.edges() if u != v )

def single_source_longest_dag_path_length(graph, s):
    assert(graph.in_degree(s) == 0)
    dist = dict.fromkeys(graph.nodes, -float('inf'))
    dist[s] = 0
    maximum = 0
    max_node = -1
    topo_order = nx.topological_sort(graph)
    for n in topo_order:
        for s in graph.successors(n):
            if dist[s] < dist[n] + 1:
                dist[s] = dist[n] + 1
                if dist[s] > maximum:
                    maximum = dist[s]
                    max_node = s
    return max_node

with open(f"instances/{sys.argv[1]}", 'w') as out_file:
    out_file.write(f"reach({node}).\n")
    out_file.write(f"0.1::delayed({node}).\n")
    out_file.write(f"0.1::delayed(Y) :- take(X,Y).\n")
    out_file.write(f"reach(Y) :- take(X,Y).\n")
    for v in network.nodes():
        children = [ u for _, u in network.out_edges(v) if u != v ]
        if len(children) > 0:
            prob = 1.0/len(children)
            out_file.write(";".join( f"{prob}::take({v},{u})" for u in children ))
            out_file.write(f":- reach({v})")
            out_file.write(f", \+ delayed({v})")
            out_file.write(".\n")
    
    query_node = single_source_longest_dag_path_length(network, node)
    query = f"reach({query_node})"
    evidence = [ f"\+reach({query_node})" ]
    available = set(network.nodes())
    available.remove(query_node)
    available.remove(node)
    negative = []
    positive = []
    while len(available) > 0 and len(evidence) < 2:
        next = random.sample([*available], 1)[0]
        if random.random() > 0.5:
            negative.append(next)
            evidence.append(f"\+reach({next})")
            available.difference_update(nx.descendants(network, next))
            available.remove(next)
        else:
            positive.append(next)
            evidence.append(f"reach({next})")
            available.intersection_update(set(nx.descendants(network, next)))

    intervention = []
    can_be_on_path = set(nx.ancestors(network, query_node))
    nr_to_sample = min(random.randint(1, len(can_be_on_path)), 2)
    for atom in random.sample([*can_be_on_path], nr_to_sample):
        intervention.append(f"reach({atom})")

import os
path = 'queries.csv'
if not os.path.exists(path):
    with open(f"queries.csv", 'a') as csvfile:
        # creating a csv writer object 
        fields = [ "file", "query", "evidence", "intervention" ]
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

# writing to csv file 
with open(f"queries.csv", 'a') as csvfile:
    # creating a csv writer object 
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow([ sys.argv[1], query, ";".join(evidence), ";".join(intervention) ])
