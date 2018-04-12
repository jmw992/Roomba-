import numpy
import options
import options
import dataPrep

rowJumpPathGen = len(dataPrep.data[0])

def nodeNumToIJ(nodeNum, rowJump):
    i = int(nodeNum/rowJump)
    j = int(nodeNum % rowJump)
    return i, j

def ijToNode(i, j, rowJump):
    return int(i*rowJump + j)

def manHattanDistanceToNode(currentNode, targetNode):
    targetI, targetJ = nodeNumToIJ(targetNode, rowJumpPathGen)
    currentI, currentJ = nodeNumToIJ(currentNode, rowJumpPathGen)

    totalDist = abs(targetI-currentI)
    totalDist += abs(targetJ-targetJ)
    return totalDist

'''
def recursivePathSrch(currentNode, depthRemain, src_sink_dict,
                      targetNode, exploredPathTpl, masterExploredPathList,
                      exploredNodesLst, masterValidSet):

    for sink in src_sink_dict[currentNode]:
        # if the arc already exists in the explored path
        if (currentNode, sink) in exploredPathTpl:
            continue
        if sink == dataPrep.charging_end_label:
            continue

        # early stopping if path couldn't make it back
        # to the root node in the number of moves remaining
        if manHattanDistanceToNode(sink, targetNode) > depthRemain+1:
            continue

        # can't cross over node that's already been visited
        if sink in exploredNodesLst:
            continue
        else:
            newExploredNodesLst = exploredNodesLst + [sink]

        newPathLst = exploredPathTpl + (currentNode, sink)


        if depthRemain > 0:
            recursivePathSrch(sink, depthRemain - 1, src_sink_dict,
                              targetNode, newPathLst, masterExploredPathList,
                              newExploredNodesLst, masterValidSet)
        else:
            if sink == targetNode:
                masterValidSet.add(newPathLst)

    return

'''

def recursivePathSrchSets(currentNode, depthRemain, src_sink_dict,
                      targetNode, exploredPathSet, masterExploredPathSet,
                      exploredNodesSet, masterValidSet):

    #early stopping if all neighbor nodes of target node have been visited
    # and length of path still remains, all entries blocked, can't make it back
    if depthRemain > 0:
        numBlockedTargetNodeNeighbors = 0
        for sink in src_sink_dict[targetNode]:
            if sink in exploredNodesSet:
                numBlockedTargetNodeNeighbors += 1
        if numBlockedTargetNodeNeighbors == len(src_sink_dict[targetNode]):
            return
        # important to free memory in recursion
        del numBlockedTargetNodeNeighbors

    for sink in src_sink_dict[currentNode]:
        # if the arc already exists in the explored path
        if (currentNode, sink) in exploredPathSet:
            continue
        if sink == dataPrep.charging_end_label:
            continue

        # early stopping if path couldn't make it back
        # to the root node in the number of moves remaining due to distance
        if manHattanDistanceToNode(sink, targetNode) > depthRemain+1:
            continue

        # can't cross over node that's already been visited
        if sink in exploredNodesSet:
            continue
        else:
            newExploredNodesSet = exploredNodesSet.union([sink])

        tmpLst = list(exploredPathSet)
        tmpLst.append((currentNode, sink))
        newPathSet = frozenset(tmpLst)


        if depthRemain > 0:
            recursivePathSrchSets(sink, depthRemain - 1, src_sink_dict,
                              targetNode, newPathSet, masterExploredPathSet,
                              newExploredNodesSet, masterValidSet)
        else:
            if sink == targetNode:
                masterValidSet.add(newPathSet)

    return


def generateSubTours(src_sink_dict):
    validSubTourSet = set()
    for pathLen in range(1, len(src_sink_dict), 2):
        masterExploredPaths = set()
        for source in src_sink_dict:
            #impossible to have charging node cycle
            if source in dataPrep.charging_nodes:
                continue

            exploredPathSet = frozenset()
            exploredNodesSet = set()

            # exploredPathLst = []
            # exploredNodesLst = []
            recursivePathSrchSets(source, pathLen, src_sink_dict,
                              source, exploredPathSet, masterExploredPaths,
                              exploredNodesSet, validSubTourSet)
        print('Finished Subtours of Len: ', pathLen,
              ' Number of Subtours Found: ', len(validSubTourSet))

    return validSubTourSet

def buildSubTourExpressions(subTourFile, source_sink_arc_dict):
    subTours = dataPrep.load_obj(subTourFile)
    expressionList = []
    constraintList = []
    for tour in subTours:
        expression = 0
        for arc in tour:
            expression += source_sink_arc_dict[arc[0]][arc[1]]
        expressionList.append(expression)
        constraintList.append(len(tour))
    return expressionList, constraintList


if __name__ == "__main__":
    validSubTourSet = generateSubTours(dataPrep.source_sink_arc_dict)
    dataPrep.save_obj(validSubTourSet, options.subTourFile)
    expressions, constraints = buildSubTourExpressions(options.subTourFile, dataPrep.source_sink_arc_dict)
    print('')



