# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 13:31:45 2018

@author: aashi

reference model
https://www.overleaf.com/13967863hyqqhcpsqdsp#/54154245/
"""

from docplex.cp.model import CpoModel
import numpy as np

data = np.load("master_data.npy")
data = data.astype(int)
# to convert above to a 2D array
data2d = np.reshape(data, (30, 900))

numericLabel = np.empty([30, 30])
invalid_nodes = []
charging_nodes = []
valid_nodes = []

charging_start_label = -1
charging_end_label = 900

def labelNodes():
    k = 0
    for i in range(len(data[0])):
        for j in range(len(data[0])):
            numericLabel[i][j] = k
            k = k + 1

    for i in range(len(data[0])):
        for j in range(len(data[0][0])):
            if (data[0][i][j] == -1):
                invalid_nodes.append(numericLabel[i][j])
            elif (data[0][i][j] == -2):
                charging_nodes.append(numericLabel[i][j])
            else:
                valid_nodes.append(numericLabel[i][j])


labelNodes()


def buildNeighborArcs(i, j):
    source_to_sinks_list = []
    #adding source node to list
    if (numericLabel[i][j] in valid_nodes):
        source_to_sinks_list.append(numericLabel[i][j])
    if (numericLabel[i][j] in charging_nodes):
        source_to_sinks_list.append(charging_end_label)

    #adding sink nodes to list checking in NSEW directions
    if ((i + 1) < len(data)):
        if (numericLabel[i + 1][j] in valid_nodes):
            source_to_sinks_list.append(numericLabel[i + 1][j])
        elif (numericLabel[i + 1][j] in charging_nodes):
            source_to_sinks_list.append(charging_end_label)
    if ((j + 1) < len(data)):
        if (numericLabel[i][j + 1] in valid_nodes):
            source_to_sinks_list.append(numericLabel[i][j + 1])
        elif (numericLabel[i][j + 1] in charging_nodes):
            source_to_sinks_list.append(charging_end_label)
    if ((i - 1) >= 0):
        if (numericLabel[i - 1][j] in valid_nodes):
            source_to_sinks_list.append(numericLabel[i - 1][j])
        elif (numericLabel[i - 1][j] in charging_nodes):
            source_to_sinks_list.append(charging_end_label)
    if ((j - 1) >= 0):
        if (numericLabel[i][j - 1] in valid_nodes):
            source_to_sinks_list.append(numericLabel[i][j - 1])
        elif ((numericLabel[i][j - 1] in charging_nodes) or (numericLabel[i - 1][j] in charging_nodes)):
            source_to_sinks_list.append(charging_end_label)
    return source_to_sinks_list

# building 2d list hold lists of [source_node, sink_node1, sink2, sink3...]
arclist = []
for i in range(0, len(data)):
    for j in range(len(data[0])):
        if numericLabel[i][j] in valid_nodes:
            arclist.append(buildNeighborArcs(i, j))
        if numericLabel[i][j] in charging_nodes:
            print("charging!!!")
            arclist.append(buildNeighborArcs(i, j))
            # 0 n+1 arc to allow not vacuming
            arclist[j].append(charging_end_label)

# print(arclist)
dirtnodelist = []
for i in range(len(data)):
    for j in range(len(data)):
        if numericLabel[i][j] in valid_nodes:
            minilist = []
            minilist.append(numericLabel[i][j])
            minilist.append(data[i][j])
            dirtnodelist.append(minilist)



# -----------------------------------------------------------------------------
# Initialize the problem data
# -----------------------------------------------------------------------------
capacity = 1000
rate_dirt_pickup = 1
numScenarios = 30

#building dictionary to connect arc source - sink to list position
arcIndex = 0
source_sink_arc_dict = {}
for nodeList in arclist:
    source_sink_arc_dict[nodeList[0]] = {}
    for i in range(1, len(nodeList)):
        source_sink_arc_dict[nodeList[0]][nodeList[i]] = arcIndex
        arcIndex += 1

sink_source_arc_dict = {}
for source in source_sink_arc_dict:
    for sink in source_sink_arc_dict[source]:
        if sink_source_arc_dict.get(sink, 'not_made') == 'not_made':
            sink_source_arc_dict[sink] = {}
            sink_source_arc_dict[sink][source] = source_sink_arc_dict[source][sink]
        else:
            sink_source_arc_dict[sink][source] = source_sink_arc_dict[source][sink]


# nested dictionary with keys [scenario][node] holding tile Index,
dirt_plusminus_dict = {}
dirt_amount_dict = {}
dirtIndex = 0
for scenario in range(numScenarios):
    dirt_plusminus_dict[scenario] = {}
    dirt_amount_dict[scenario] = {}
    for nodeList in arclist:
        if nodeList[0] == charging_end_label or nodeList[0] == charging_start_label:
            continue
        dirt_plusminus_dict[scenario][int(nodeList[0])] = dirtIndex
        dirt_amount_dict[scenario][int(nodeList[0])] = data2d[scenario][int(nodeList[0])]
        dirtIndex += 1

# -----------------------------------------------------------------------------
# Build the model and variables
# -----------------------------------------------------------------------------

# Create CPO model
mdl = CpoModel()

# x_ij = mdl.binary_var_dict((source, sink) for source in )
num_arcs = 0
for arc in arclist:
    num_arcs = num_arcs + len(arc) - 1

decision_Arcs = mdl.binary_var_list(num_arcs, name='arc')

# nested integer_cplex_list for dis+, dis-,
decision_dirt_plus = mdl.integer_var_list(len(valid_nodes) * numScenarios, min=0, name='dplus')
decision_dirt_minus = mdl.integer_var_list(len(valid_nodes) * numScenarios, min=0, name='dminus')

# -----------------------------------------------------------------------------
# Build the constraints
# -----------------------------------------------------------------------------

# constraint 2, 3
for source in source_sink_arc_dict:
    arc_sum_expression = 0
    for sink in source_sink_arc_dict[source]:
        arc_sum_expression += decision_Arcs[source_sink_arc_dict[source][sink]]

    # constraint 3 : must leave the charging station
    if source ==charging_start_label:
        mdl.add(arc_sum_expression == 1)
        print("constrint 3 entered")

    # constraint 2 : Each tile can be vaumed at most once (can only leave from a tile once)
    else:
        mdl.add(arc_sum_expression <= 1)

# constraint 4 : the arc must return to the charging station
arc_sum_expression = 0
for source in sink_source_arc_dict[charging_end_label]:
    arc_sum_expression += decision_Arcs[sink_source_arc_dict[charging_end_label][source]]

mdl.add(arc_sum_expression == 1)

# constraint 5 : the roomba leaves node k, k elment of Tl, if and only if it enters that node
for tile in source_sink_arc_dict:
    source_arc_sum = 0
    sink_arc_sum = 0

    if(tile == charging_end_label or tile == charging_start_label):
        continue
    for sink in source_sink_arc_dict[tile]:
        source_arc_sum += decision_Arcs[source_sink_arc_dict[tile][sink]]

    for source in sink_source_arc_dict[tile]:
        sink_arc_sum += decision_Arcs[sink_source_arc_dict[tile][source]]
    mdl.add(sink_arc_sum == source_arc_sum)

# constraint 6 : the roomba cannot pickup more dirt than its capacity permits
dirt_collected_sum = 0
for source in source_sink_arc_dict:
    for sink in source_sink_arc_dict[source]:
        dirt_collected_sum += rate_dirt_pickup*decision_Arcs[source_sink_arc_dict[source][sink]]

mdl.add(dirt_collected_sum == 1)


# constraint 7 : Balance for the dirt on each tile under each scenario
for source in source_sink_arc_dict:
    if source == charging_start_label or source == charging_end_label:
        continue
    sum_vacumed = 0
    for sink in source_sink_arc_dict[source]:
        sum_vacumed += decision_Arcs[source_sink_arc_dict[source][sink]]
    sum_vacumed *= rate_dirt_pickup

    for scenario in range(numScenarios):
        scenario_balanced = sum_vacumed \
                            + decision_dirt_minus[dirt_plusminus_dict[scenario][source]] \
                            - decision_dirt_plus[dirt_plusminus_dict[scenario][source]]

        mdl.add(scenario_balanced == dirt_amount_dict[scenario][source])


# -----------------------------------------------------------------------------
# Objective function
# -----------------------------------------------------------------------------
objectiveSum = 0
for i in range(len(decision_dirt_minus)):
    objectiveSum = decision_dirt_minus[i] + decision_dirt_plus[i]

mdl.add(mdl.minimize(objectiveSum))
# -----------------------------------------------------------------------------
# Solve the Model
# -----------------------------------------------------------------------------
print("Solving model....")
msol = mdl.solve(FailLimit=1000, TimeLimit=100000000)


print('done')
'''
for s in range(MAX_SLABS):
   su = 0
   for c in allcolors:
       lo = False
       for i, o in enumerate(ORDERS):
           if o.color == c:
               lo |= (production_slab[i] == s)
       su += lo
   mdl.add(su <= MAX_COLOR_PER_SLAB)
'''