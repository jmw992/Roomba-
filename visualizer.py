# -*- coding: utf-8 -*-
"""
Created on Sun Apr  8 13:00:10 2018
@author: aashi
"""

import numpy as np
import matplotlib as mlp
import matplotlib.pyplot as pyplot


def visualizePath(data, path, visualFrequency=5):
    grid = np.copy(data)
    maxDirt = np.amax(grid)

    # Bounds will be [chargin station, wall, dirt levelx4, vacuumed]
    cmap = mlp.colors.ListedColormap(['Green', 'Black', 'Red', 'White', 'Yellow', 'Orange', 'Pink', 'Blue'])
    bounds = [-3, -1.1, -0.1, int(maxDirt*.2), int(maxDirt*.4), int(maxDirt*.6), int(maxDirt*.8), maxDirt+.1, 100]

    lastSink = path[0][0]
    for i in range(len(path)):
        #if the sink from the last node doesn't equal the source
        if lastSink != path[i][0]:
            print('Sink-Source Mismatch Bad Error')
            return

        grid[int(path[i][0] / len(grid))][int(path[i][0] % len(grid))] = 99
        lastSink = path[i][1]
        if i % visualFrequency == 0:
            norm = mlp.colors.BoundaryNorm(bounds, cmap.N)
            img = pyplot.imshow(grid, interpolation='nearest',
                                        cmap = cmap, norm = norm)
            pyplot.show()
    print('Done Charging Start Path')
def visualizeVacuumed(data, vacuumedArcs):
    grid = np.copy(data)
    maxDirt = np.amax(grid)

    # Bounds will be [chargin station, wall, dirt levelx4, vacuumed]
    cmap = mlp.colors.ListedColormap(['Green', 'Black', 'Red', 'White', 'Yellow', 'Orange', 'Pink', 'Blue'])
    bounds = [-3, -1.1, -0.1, int(maxDirt*.2), int(maxDirt*.4), int(maxDirt*.6), int(maxDirt*.8), maxDirt+.1, 100]

    for node in vacuumedArcs:
        grid[int(node / len(grid))][int(node % len(grid))] = 99

    norm = mlp.colors.BoundaryNorm(bounds, cmap.N)
    img = pyplot.imshow(grid, interpolation='nearest',
                        cmap=cmap, norm=norm)
    pyplot.show()
    print('Done Showing All Vacuumed Path')