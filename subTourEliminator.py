import numpy
import options

def nodeNumToIJ(nodeNum, rowJump):
    i = int(nodeNum/rowJump)
    j = int(nodeNum % rowJump)
    return i, j

def ijToNode(i, j, rowJump):
    return int(i*rowJump + j)

def cornerIJ(nodeNum, x, y, rowJump):
    bottomI, bottomJ = nodeNumToIJ(nodeNum, rowJump)
    i = bottomI + int(x)
    j = bottomJ + int(y)
    return i, j

#will return a list of cplex expressions for all of the different neighbor combinations
def neigbhorCyclingCheck(checkNode, source_sink_dict, dec_arc_lst, setOfCheckedNeighborSets):
    print('')
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

#assume will be fed valid check node
def twoByTwoCyclingCheck(checkNode, grid, source_sink_arc_dict, dec_arc_lst):
    print('')
    expression = 0
    twoBytwoNodes = {checkNode}
    rowjump = len(grid)
    iTop, jTop = cornerIJ(checkNode, 2, 2, rowjump)
    if iTop >= rowjump or jTop >= rowjump:
        return expression

    iCheck, jCheck = nodeNumToIJ(checkNode, rowjump)
    for i in range(iCheck, iTop):
        for j in range(jCheck, jTop):
            if grid[i, j] > 0:
                twoBytwoNodes.add(ijToNode(i, j, rowjump))

    # if not all nodes are included the non cycling will be handled
    # by the neighbor check, so don't add unnecessary constraint
    '''
    if len(twoBytwoNodes) < 4:
        return expression
    '''

    for node in twoBytwoNodes:
        for sink in source_sink_arc_dict[node]:
            if sink not in twoBytwoNodes:
                expression += dec_arc_lst[source_sink_arc_dict[node][sink]]

    return expression

def twoByTwoCyclingExprListBuilder(grid, source_sink_dict, dec_arc_lst):
    expressionList = []
    for source in source_sink_dict:
        expressionList.append(twoByTwoCyclingCheck(source, grid, source_sink_dict, dec_arc_lst))
    return expressionList

#handles checking a square of width X and Height Y to make sure it is not
# check node is bottom corner, will build X and Y rectangle grid from there
def xByYcyclingExpressionCheck(checkNode, x, y, grid, source_sink_arc_dict, dec_arc_lst):
    print('')
    expression = 0
    xByYnodes = {checkNode}
    edgeNodes = {checkNode}

    rowjump = len(grid)
    iTop, jTop = cornerIJ(checkNode, x, y, rowjump)

    #if you've gone out of bounds, will be handled by smaller case
    if iTop >= rowjump or jTop >= rowjump:
        return expression

    iCheck, jCheck = nodeNumToIJ(checkNode, rowjump)
    for i in range(iCheck, iTop):
        for j in range(jCheck, jTop):
            if grid[i, j] > 0:
                xByYnodes.add(ijToNode(i, j, rowjump))

    '''
    # if not all nodes are included the non cycling will be handled
    # by a smaller unit check so don't add unnecessary constraint
    if len(xByYnodes) < x*y:
        return expression

    for i in range(iCheck, iCheck + x):
        if source_sink_arc_dict.get(ijToNode(i, jCheck, rowjump), False):
            edgeNodes.add(ijToNode(i, jCheck, rowjump))
        if source_sink_arc_dict.get(ijToNode(i, jTop, rowjump), False):
            edgeNodes.add(ijToNode(i, jTop, rowjump))
    for j in range(jCheck, jTop + y):
        if source_sink_arc_dict.get(ijToNode(iCheck, j, rowjump), False):
            edgeNodes.add(ijToNode(i, jCheck, rowjump))
        if source_sink_arc_dict.get(ijToNode(iTop, j, rowjump), False):
            edgeNodes.add(ijToNode(i, jTop, rowjump))
    '''

    for node in xByYnodes:
        for sink in source_sink_arc_dict[node]:
            if sink not in xByYnodes:
                expression += dec_arc_lst[source_sink_arc_dict[node][sink]]

    return expression

def xByYcyclingExprListBuilder(grid, x, y, source_sink_dict, dec_arc_lst):
    expressionList = []
    for source in source_sink_dict:
        expressionList.append(xByYcyclingExpressionCheck(source, x, y, grid, source_sink_dict, dec_arc_lst))
    return expressionList

def rectangleCyclingExprListBuilder(grid, source_sink_dict, dec_arc_lst):
    print('')
    expressionList = []
    for x in range(3, len(grid)):
        expressionList += xByYcyclingExprListBuilder(grid, x, x-1, source_sink_dict, dec_arc_lst)
        expressionList += xByYcyclingExprListBuilder(grid, x-1, x, source_sink_dict, dec_arc_lst)
        expressionList += xByYcyclingExprListBuilder(grid, x, x, source_sink_dict, dec_arc_lst)

    return expressionList

def masterSubTourEliminator(grid, source_sink_arc_dict, dec_arc_lst):
    print('')
    expressionList = []
    trimmedExpressionList = []
    #checking

    expressionList += neighborCyclingExprListBuilder(source_sink_arc_dict, dec_arc_lst)

    expressionList += twoByTwoCyclingExprListBuilder(grid, source_sink_arc_dict, dec_arc_lst)

    expressionList += rectangleCyclingExprListBuilder(grid, source_sink_arc_dict, dec_arc_lst)

    for expression in expressionList:
        if type(expression) != int:
            trimmedExpressionList.append(expression)
    return trimmedExpressionList
