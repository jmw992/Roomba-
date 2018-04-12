import numpy as np
import options
import pickle

def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

if options.dirtFile[-3:]=='npy':
    data = np.load(options.dirtFile)
elif options.dirtFile[-3:]=='csv':
    data = np.loadtxt(options.dirtFile, delimiter=',')

data = data.astype(int)
# to convert above to a 2D array
data2d = np.reshape(data, (options.numScenarios, len(data[0])*len(data[0])))


numericLabel = np.empty([len(data[0]), len(data[0])])
invalid_nodes = []
charging_nodes = []
valid_nodes = []


charging_start_label = options.charging_start_value
charging_end_label = options.charging_end_label

def orderedPathMaker(path_dict, start_node):
    path_list = []
    source = start_node

    while True:
        sink = path_dict[source]
        path_list.append((source,sink))
        if sink == charging_end_label:
            break
        else:
            source = sink

    return path_list

def labelNodes():
    k = 0
    for i in range(len(data[0])):
        for j in range(len(data[0][0])):
            numericLabel[i][j] = k
            k = k + 1

    for i in range(len(data[0])):
        for j in range(len(data[0][0])):
            if (data[0][i][j] == -1):
                invalid_nodes.append(numericLabel[i][j])
            elif (data[0][i][j] == -2):
                charging_start_label = numericLabel
                charging_nodes.append(numericLabel[i][j])
            else:
                valid_nodes.append(numericLabel[i][j])


labelNodes()


def buildNeighborArcs(i, j):
    source_to_sinks_list = []
    #adding source node to list
    if (numericLabel[i][j] in valid_nodes):
        source_to_sinks_list.append(numericLabel[i][j])
    elif (numericLabel[i][j] in charging_nodes):
        source_to_sinks_list.append(numericLabel[i][j])

    #adding sink nodes to list checking in NSEW directions
    if ((i + 1) < len(data[0])):
        if (numericLabel[i + 1][j] in valid_nodes):
            source_to_sinks_list.append(numericLabel[i + 1][j])
        elif (numericLabel[i + 1][j] in charging_nodes):
            source_to_sinks_list.append(charging_end_label)
    if ((j + 1) < len(data[0])):
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
    if numericLabel[i][j] == 9:
        print('?')
    return source_to_sinks_list

# building 2d list hold lists of [source_node, sink_node1, sink2, sink3...]
arclist = []

for i in range(0, len(data[0])):
    for j in range(len(data[0])):
        if numericLabel[i][j] in valid_nodes:
            arclist.append(buildNeighborArcs(i, j))

        # 0 n+1 arc to allow not vacuming
        if numericLabel[i][j] in charging_nodes:
            print("charging!!!")
            chargeNeighbors = buildNeighborArcs(i, j)
            chargeNeighbors.append(charging_end_label)
            arclist.append(chargeNeighbors)


# print(arclist)
dirtnodelist = []
for i in range(len(data[0])):
    for j in range(len(data[0])):
        if numericLabel[i][j] in valid_nodes:
            minilist = []
            minilist.append(numericLabel[i][j])
            minilist.append(data[i][j])
            dirtnodelist.append(minilist)

oomba_dirt_capacity = options.roomba_dirt_capacity
rate_dirt_pickup = options.rate_dirt_pickup
numScenarios = options.numScenarios

#building dictionary to connect arc source - sink to list position
arcIndex = 0
source_sink_arc_dict = {}   #key: source value: dict{key: sink  value: arc_index}
index_arc_dict = {}         #key: index  value: (source, sink)
for nodeList in arclist:
    source_sink_arc_dict[nodeList[0]] = {}
    for i in range(1, len(nodeList)):
        source_sink_arc_dict[nodeList[0]][nodeList[i]] = arcIndex
        index_arc_dict[arcIndex] = (nodeList[0], nodeList[i])
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
        if nodeList[0] == charging_end_label or nodeList[0] in charging_nodes:
            continue
        dirt_plusminus_dict[scenario][int(nodeList[0])] = dirtIndex
        dirt_amount_dict[scenario][int(nodeList[0])] = data2d[scenario][int(nodeList[0])]
        dirtIndex += 1

# x_ij = mdl.binary_var_dict((source, sink) for source in )
num_arcs = 0
for arc in arclist:
    num_arcs = num_arcs + len(arc) - 1

