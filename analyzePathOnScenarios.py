# File created by jacob williams
import dataPrep
import options

def nodeNumToIJ(nodeNum, rowJump):
    i = int(nodeNum/rowJump)
    j = int(nodeNum % rowJump)
    return i, j

def ijToNode(i, j, rowJump):
    return int(i*rowJump + j)

def analyzePathAcrossScenarios(followedPathLst, amountVacuumed):
    totalVacuumed = 0
    totalLeftBehind = 0
    totalOverVacuumed = 0
    for tple in followedPathLst:
        i, j = nodeNumToIJ(tple[0], len(dataPrep.data[0]))
        if tple[0] in dataPrep.charging_nodes:
            continue
        if tple[1] == options.charging_end_label:
            continue
        for scenario in range(len(dataPrep.data)):
            nodeDirtAmount = dataPrep.data[scenario][i][j]
            if nodeDirtAmount - amountVacuumed[tple[0]] >= 0:
                totalLeftBehind += nodeDirtAmount - amountVacuumed[tple[0]]
                totalVacuumed += amountVacuumed[tple[0]]
            else:
                totalOverVacuumed += amountVacuumed[tple[0]] - nodeDirtAmount
                totalVacuumed += nodeDirtAmount

    return totalVacuumed, \
           totalLeftBehind, \
           totalOverVacuumed