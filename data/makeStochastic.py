import numpy as np

def changeDirtLevel(dirtLevel):
    #if the wall is a charging station or wall
    if dirtLevel < 0:
        return dirtLevel
    else:
        newLevel = dirtLevel + np.random.randint(-4, high=4)
        if newLevel < 0:
            return 0
        else:
            return newLevel

#this program will take a 2-D floor plan and create a 3d numpy array
# of stochastic scenarios
wallLabel = -1
chargingLabel = -2
numScenarios = 10
inputFile = 'small_floor.csv'
outputFile = 'small_floor10scenarios'

originalFloor = np.loadtxt(inputFile, delimiter=',')

scenarioList = [originalFloor]

for s in range(numScenarios-1):
    scenarioFloor = np.copy(originalFloor)
    for i in range(len(originalFloor)):
        for j in range(len(originalFloor[i])):
            scenarioFloor[i, j] = changeDirtLevel(originalFloor[i,j])
    scenarioList.append(scenarioFloor)

scenarioList = np.array(scenarioList)

np.save(outputFile, scenarioList)