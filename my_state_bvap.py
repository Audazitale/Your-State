import csv
import os
from functools import partial
import json
import numpy as np
import geopandas as gpd
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


from gerrychain import (
    Election,
    Graph,
    MarkovChain,
    Partition,
    accept,
    constraints,
    updaters,
)
from gerrychain.metrics import efficiency_gap, mean_median
from gerrychain.proposals import recom, propose_random_flip
from gerrychain.updaters import cut_edges
from gerrychain.tree import recursive_tree_part


def draw_plot(data, offset, edge_color, fill_color):
    pos = 10*np.arange(data.shape[1])+1+offset
    #bp = ax.boxplot(data, positions= pos, widths=0.3, patch_artist=True, manage_xticks=False)
    bp = ax.boxplot(data, positions= pos,widths=.18, whis=[1,99],showfliers=False, patch_artist=True, manage_xticks=False,zorder=4)
    for element in ['boxes', 'whiskers', 'medians', 'caps']:
        plt.setp(bp[element], color=edge_color,zorder=4)
    for patch in bp['boxes']:
        patch.set(facecolor=fill_color,zorder=4)

state_abbr = "AR"
state_fip = "05"
num_districts = 4



newdir = "./Outputs/"+state_abbr+"/"
os.makedirs(os.path.dirname(newdir + "init.txt"), exist_ok=True)
with open(newdir + "init.txt", "w") as f:
    f.write("Created Folder")
    
County_graph = Graph.from_json("./County/dual_graphs/County"+state_fip+".json")
COUSUB_graph = Graph.from_json("./County_Subunits/COUSUB"+state_fip+".json")
Tract_graph = Graph.from_json("./Tracts/Tract"+state_fip+".json")
BG_graph = Graph.from_json("./Tracts/Tract"+state_fip+".json")#("./Block_Group/BG"+state_fip+".json")

unique_label = "GEOID10"
pop_col = "TOTPOP"

graph_list = [County_graph,COUSUB_graph,Tract_graph,BG_graph]

vap_list = ["VAP","VA","VAP","VAP"]
totpop = [0,0,0,0]
for i in range(4):
    graph=graph_list[i]
    
    for n in graph.nodes():
        graph.node[n]["BVAP"] = int(graph.node[n]["BVAP"])
        graph.node[n][vap_list[i]] = int(graph.node[n][vap_list[i]])
        graph.node[n]["TOTPOP"] = int(graph.node[n]["TOTPOP"])
        totpop[i] += graph.node[n]["TOTPOP"]
        
        graph.node[n]["nBVAP"] = graph.node[n][vap_list[i]]- graph.node[n]["BVAP"]

starts = []
for i in range(4):
    starts.append(recursive_tree_part(graph_list[i],range(num_districts),totpop[i]/num_districts,"TOTPOP", .02,1))
    
updater = {
        "population": updaters.Tally("TOTPOP", alias="population"),
    "cut_edges": cut_edges,
    "BVAP":Election("BVAP",{"BVAP":"BVAP","nBVAP":"nBVAP"})
}



initial_partitions = []
proposals = []
compactness_bounds = []
chains=[]

for i in range(4):
    initial_partitions.append(Partition(graph_list[i],starts[i], updater))


    proposals.append(partial(
        recom, pop_col="TOTPOP", pop_target=totpop[i]/num_districts, epsilon=0.02, node_repeats=1
    ))

    compactness_bounds.append(constraints.UpperBound(
        lambda p: len(p["cut_edges"]), 2 * len(initial_partitions[i]["cut_edges"])
    ))

    chains.append(MarkovChain(
        proposal=proposals[i],
        constraints=[
            constraints.within_percent_of_ideal_population(initial_partitions[i], 0.05),compactness_bounds[i]
          #constraints.single_flip_contiguous#no_more_discontiguous
        ],
        accept=accept.always_accept,
        initial_state=initial_partitions[i],
        total_steps=100
    ))

cuts=[[],[],[],[]]
BVAPS=[[],[],[],[]]

for i in range(4):
    t = 0
    for part in chains[i]:
        cuts[i].append(len(part["cut_edges"]))
        BVAPS[i].append(sorted(part["BVAP"].percents("BVAP")))
        t+=1
        if t%10 ==0:
            print("chain",i,"step",t)
    print(f"finished chain {i}")


colors = ['hotpink','goldenrod','green','purple']
labels= ['County','COUSUB','Tract','Block Group']
plt.figure()
for i in range(4):
    sns.distplot(cuts[i],kde=False, color=colors[i],label=labels[i])
plt.legend()
plt.ylabel("Cut Edges")
plt.show()

fig, ax = plt.subplots()
draw_plot(np.array(BVAPS[0]),-3,colors[0],None)
draw_plot(np.array(BVAPS[1]),-1,colors[1],None)
draw_plot(np.array(BVAPS[2]),1,colors[2],None)
draw_plot(np.array(BVAPS[3]),3,colors[3],None)
plt.ylabel("BVAP%")
for i in range(4):
    plt.plot([],[],color=colors[i],label=labels[i])
plt.legend()
plt.show()

        
