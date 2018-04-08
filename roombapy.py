# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 13:31:45 2018
@author: aashi
reference model
https://www.overleaf.com/13967863hyqqhcpsqdsp#/54154245/
"""

from docplex.cp.model import CpoModel
import options
import dataPrep

numScenarios = options.numScenarios
charging_end_label = options.charging_end_label
roomba_dirt_capacity = options.roomba_dirt_capacity
rate_dirt_pickup = options.rate_dirt_pickup

charging_nodes = dataPrep.charging_nodes
source_sink_arc_dict = dataPrep.source_sink_arc_dict
sink_source_arc_dict = dataPrep.sink_source_arc_dict
dirt_plusminus_dict = dataPrep.dirt_plusminus_dict
dirt_amount_dict = dataPrep.dirt_amount_dict
index_arc_dict = dataPrep.index_arc_dict
num_arcs = dataPrep.num_arcs
# -----------------------------------------------------------------------------
# Build the model and variables
# -----------------------------------------------------------------------------

# Create CPO model
mdl = CpoModel()

decision_Arcs = mdl.binary_var_list(dataPrep.num_arcs, name='arc')

# nested integer_cplex_list for dis+, dis-,
decision_dirt_plus = mdl.integer_var_list(len(dataPrep.valid_nodes) * numScenarios, min=0, name='dplus')
decision_dirt_minus = mdl.integer_var_list(len(dataPrep.valid_nodes) * numScenarios, min=0, name='dminus')

# -----------------------------------------------------------------------------
# Build the constraints
# -----------------------------------------------------------------------------

# constraint 2, 3
for source in source_sink_arc_dict:
    arc_sum_expression = 0
    for sink in source_sink_arc_dict[source]:
        arc_sum_expression += decision_Arcs[source_sink_arc_dict[source][sink]]

    # constraint 3 : must leave the charging station
    if source in charging_nodes:
        mdl.add(arc_sum_expression == 1)
        print("constraint 3 entered")

    # constraint 2 : Each tile can be vacumed at most once (can only leave from a tile once)
    else:
        mdl.add(arc_sum_expression <= 1)

# constraint 4 : the arc must return to the charging station
end_charging_arcs_sum = 0
for source in sink_source_arc_dict[charging_end_label]:
    end_charging_arcs_sum += decision_Arcs[sink_source_arc_dict[charging_end_label][source]]

mdl.add(end_charging_arcs_sum == 1)

# constraint 5 : the roomba leaves node k, k elment of Tl, if and only if it enters that node
for tile in source_sink_arc_dict:
    source_arc_sum = 0
    sink_arc_sum = 0

    if(tile == charging_end_label or tile in charging_nodes):
        print('constraint 5 charging end label encountered and skipped')
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
        dirt_collected_sum += decision_Arcs[source_sink_arc_dict[source][sink]]

mdl.add(rate_dirt_pickup * dirt_collected_sum <= roomba_dirt_capacity)

# constraint 7 : Balance for the dirt on each tile under each scenario
for source in source_sink_arc_dict:
    if (source in charging_nodes) or (source == charging_end_label):
        print('constraint 7, chargin node skipped')
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
    objectiveSum += decision_dirt_minus[i] + decision_dirt_plus[i]

mdl.add(mdl.minimize(objectiveSum))

'''
objectiveSum = 0
for i in range(len(decision_Arcs)):
    objectiveSum += decision_Arcs[i]

mdl.add(mdl.maximize(objectiveSum))
'''
# -----------------------------------------------------------------------------
# Solve the Model
# -----------------------------------------------------------------------------
print("Solving model....")
msol = mdl.solve(TimeLimit = options.solverTimeLimit)

if msol:
    print('Solution Found')
    solution_arcs = []
    roomba_path = {}    #will have key: source Value: sink
    for arcIndex in range(num_arcs):
        solution_arcs.append(msol[decision_Arcs[arcIndex]])
        if (solution_arcs[arcIndex] > 0):
            src_sink_tple = index_arc_dict[arcIndex]
            roomba_path[src_sink_tple[0]] = src_sink_tple[1]

    print(sum(solution_arcs))
    # solution_dirt_plus = msol[decision_dirt_plus]
    # solution_dirt_minus = msol[decision_dirt_minus]
    print('Done')
else:
    print('No solution Found')
