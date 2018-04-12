import numpy
import options
import dataPrep

def nodeNumToIJ(nodeNum, rowJump):
    i = int(nodeNum/rowJump)
    j = int(nodeNum % rowJump)
    return i, j

def ijToNode(i, j, rowJump):
    return int(i*rowJump + j)

def cornerIJ(nodeNum, x, y, rowJump):
    bottomI, bottomJ = nodeNumToIJ(nodeNum, rowJump)
    i = bottomI + int(x)-1
    j = bottomJ + int(y)-1
    return i, j

#will return a list of cplex expressions for all of the different neighbor combinations
def neigbhorCyclingCheck(checkNode, source_sink_dict, dec_arc_lst, setOfCheckedNeighborSets):
    expressionList = []
    for neighbor in source_sink_dict[checkNode]:
        if neighbor == options.charging_end_label:
            continue
        expression = 0
        neighborNodes = frozenset([checkNode, neighbor])

        #handles checking neighbors coming from other direction
        # will be equivalent and double the constraints created
        if neighborNodes in setOfCheckedNeighborSets:
            continue
        setOfCheckedNeighborSets.add(neighborNodes)
        for node in neighborNodes:
            for sink in source_sink_dict[node]:
                if sink not in neighborNodes:
                    arcIndex = source_sink_dict[node][sink]
                    expression += dec_arc_lst[arcIndex]
        expressionList.append(expression)
    return expressionList

def neighborCyclingExprListBuilder(source_sink_dict, dec_arc_lst):
    expressionList = []
    setOfCheckedNeigborSets = set()
    for key in source_sink_dict:
        if key == options.charging_end_label:
            continue
        expressionList += neigbhorCyclingCheck(key, source_sink_dict, dec_arc_lst, setOfCheckedNeigborSets)
    return expressionList

#handles checking a square of width X and Height Y to make sure it is not
# check node is bottom corner, will build X and Y rectangle grid from there
def xByYcyclingExpressionCheck(checkNode, x, y, grid, source_sink_arc_dict, dec_arc_lst, exploredSubtorSets):
    expression = 0
    xByYnodes = {checkNode}

    rowjump = len(grid)
    iTop, jTop = cornerIJ(checkNode, x, y, rowjump)

    iCheck, jCheck = nodeNumToIJ(checkNode, rowjump)
    for i in range(iCheck, iTop):
        for j in range(jCheck, jTop):
            #if either index is out of bounds
            if i >= rowjump or j >= rowjump:
                continue
            # if not a wall or it is the charging station
            if grid[i, j] > 0 or grid[i, j] == options.charging_start_value:
                xByYnodes.add(ijToNode(i, j, rowjump))

    #if there's only one node or less in a set
    if len(xByYnodes) <= 1:
        return expression

    xByYnodes = frozenset(xByYnodes)
    #if this subtour has been explored already
    if xByYnodes in exploredSubtorSets:
        return expression
    else:
        exploredSubtorSets.add(xByYnodes)

    for node in xByYnodes:
        for sink in source_sink_arc_dict[node]:
            if sink not in xByYnodes:
                arcIndex = source_sink_arc_dict[node][sink]
                expression += dec_arc_lst[arcIndex]

    return expression

def xByYcyclingExprListBuilder(grid, x, y, source_sink_dict, dec_arc_lst, exploredSubtorSets):
    expressionList = []
    for source in source_sink_dict:
        expressionList.append(
            xByYcyclingExpressionCheck(source, x, y, grid, source_sink_dict, dec_arc_lst, exploredSubtorSets))
    return expressionList

def rectangleCyclingExprListBuilder(grid, source_sink_dict, dec_arc_lst):
    print('')
    exploredSubtourSets = set()
    expressionList = []
    for x in range(2, len(grid)):
        for y in range(2, len(grid)):
            # can't have single node constraints
            expressionList += xByYcyclingExprListBuilder(grid, x, y,
                                                         source_sink_dict, dec_arc_lst, exploredSubtourSets)

    return expressionList

def masterSubTourEliminator(grid, source_sink_arc_dict, dec_arc_lst):
    expressionList = []
    trimmedExpressionList = []
    #checking

    expressionList += neighborCyclingExprListBuilder(source_sink_arc_dict, dec_arc_lst)

    #expressionList += twoByTwoCyclingExprListBuilder(grid, source_sink_arc_dict, dec_arc_lst)

    expressionList += rectangleCyclingExprListBuilder(grid, source_sink_arc_dict, dec_arc_lst)

    for expression in expressionList:
        if type(expression) != int:
            trimmedExpressionList.append(expression)
    return trimmedExpressionList
