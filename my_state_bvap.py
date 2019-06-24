import csv
import os
from functools import partial
import json
import numpy as np
import geopandas as gpd
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt


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


state_abbr = "AR"
state_fip = "05"
num_districts = 4



newdir = "./Outputs/"+state_abbr+housen+"_BG/"
os.makedirs(os.path.dirname(newdir + "init.txt"), exist_ok=True)
with open(newdir + "init.txt", "w") as f:
    f.write("Created Folder")
    
County_graph = Graph.from_json("./County/dual_graphs/County"+state_fip+".json")
COUSUB_graph = Graph.from_json("./County_Subunits/COUSUB"+state_fip+".json")
Tract_graph = Graph.from_json("./Tracts/Tract"+state_fip+".json")
BG_graph = Graph.from_json("./Block_Group/BG"+state_fip+".json")
