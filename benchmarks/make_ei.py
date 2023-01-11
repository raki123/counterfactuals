import sys
import networkx as nx
import random
import csv
import os

n = int(sys.argv[1])
k = int(sys.argv[2])
tree = nx.random_tree(n, create_using=nx.DiGraph)


network = nx.DiGraph() 
extra_nodes = list(range(n, n + k))
final_node = n + k + 1
for node in tree.nodes():
    network.add_edges_from( (node,v) for v in extra_nodes)
    network.add_edges_from( (node,v) for _, v in tree.out_edges(node))

for node in extra_nodes:
    network.add_edge(node, final_node)


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

with open(f"ei_instances/tree_{n}_{k}.lp", 'w') as out_file:
    out_file.write(f"reach(0).\n")
    out_file.write(f"0.1::delayed(0).\n")
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
    

query_node = final_node
query = f"reach({query_node})"
neg_evidence = []
while len(neg_evidence) < 5:
    neg_evidence = []
    available = set(network.nodes())
    available.remove(query_node)
    available.remove(node)
    negative = []
    positive = []
    while len(available) > 0 and len(neg_evidence) < 5:
        next = random.sample([*available], 1)[0]
        negative.append(next)
        neg_evidence.append(f"\+reach({next})")
        available.difference_update(nx.descendants(network, next))
        available.remove(next)
                

query_node = final_node
query = f"reach({query_node})"
pos_evidence = []
while len(pos_evidence) < 5:
    pos_evidence = []
    available = set(network.nodes())
    available.remove(query_node)
    available.remove(node)
    negative = []
    positive = []
    while len(available) > 0 and len(pos_evidence) < 5:
        next = random.sample([*available], 1)[0]
        positive.append(next)
        pos_evidence.append(f"reach({next})")
        available.intersection_update(set(nx.descendants(network, next)))

pos_intervention = []
neg_intervention = []
can_be_on_path = set(nx.ancestors(network, query_node))
for atom in random.sample([*can_be_on_path], 5):
    pos_intervention.append(f"reach({atom})")
    neg_intervention.append(f"\+reach({atom})")

path = 'ei_queries.csv'
if not os.path.exists(path):
    with open(f"ei_queries.csv", 'a') as csvfile:
        # creating a csv writer object 
        fields = [ "file", "query", "evidence", "intervention" ]
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

# writing to csv file 
with open(f"ei_queries.csv", 'a') as csvfile:
    # creating a csv writer object 
    csvwriter = csv.writer(csvfile)
    for e in range(-5, 6, 1):
        for i in range(-5, 6, 1):
            if e > 0:
                evidence = [ f"\+reach({query_node})" ] + pos_evidence[:e]
            else:
                evidence = [ f"\+reach({query_node})" ] + neg_evidence[:abs(e)]

            if i > 0:
                intervention = pos_intervention[:i]
            else:
                intervention = neg_intervention[:abs(i)]
            
            csvwriter.writerow([ f"tree_{n}_{k}.lp", query, ";".join(evidence), ";".join(intervention) ])
