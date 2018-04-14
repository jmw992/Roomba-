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
import visualizer
import subTourEliminator
import subTourGeneration as stg

numScenarios = options.numScenarios
charging_end_label = options.charging_end_label
roomba_dirt_capacity = options.roomba_dirt_capacity

rate_dirt_pickup = dataPrep.constant_dirt_vacuuming_rate
vacuumed_at_node= dataPrep.vacuumed_Amount_dict
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
decision_dirt_minus = mdl.integer_var_list(len(dataPrep.valid_nodes) * numScenarios, min=0, max=1000, name='dminus')

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
    if source in charging_nodes:
        continue
    for sink in source_sink_arc_dict[source]:
        if sink == charging_end_label:
            continue
        dirt_collected_sum += vacuumed_at_node[source]*decision_Arcs[source_sink_arc_dict[source][sink]]

mdl.add(dirt_collected_sum <= roomba_dirt_capacity)

# constraint 7 : Balance for the dirt on each tile under each scenario
for source in source_sink_arc_dict:
    if (source in charging_nodes):
        print('constraint 7, charging node skipped')
        continue
    sum_vacumed = 0
    for sink in source_sink_arc_dict[source]:
        if(sink == charging_end_label):
            print('constraint 7, sink node skipped')
            continue
        sum_vacumed += decision_Arcs[source_sink_arc_dict[source][sink]] * vacuumed_at_node[source]

    for scenario in range(numScenarios):
        scenario_balanced = sum_vacumed \
                            + decision_dirt_minus[dirt_plusminus_dict[scenario][source]] \
                            - decision_dirt_plus[dirt_plusminus_dict[scenario][source]]

        mdl.add(scenario_balanced == dirt_amount_dict[scenario][source])

# constraint 8: Subtour Elimination, subset, must make sure
# that the sum of nodes leaving the subest is greater than or equal to one
# so no cycling occurs
subTours = dataPrep.load_obj(options.subTourFile)
for tour in subTours:
    expression = 0
    numArcs = 0
    for arc in tour:
        expression += decision_Arcs[source_sink_arc_dict[arc[0]][arc[1]]]
        numArcs += 1
    mdl.add(expression < numArcs)

# constraint 9: Limited time
# time spent
time_spent_cleaning = 0
for source in source_sink_arc_dict:
    if (source in charging_nodes):
        print('constraint 9, charging node skipped')
        time_spent_cleaning += options.time_to_move
        continue
    sum_vacumed = 0
    for sink in source_sink_arc_dict[source]:
        time_spent_cleaning += decision_Arcs[source_sink_arc_dict[source][sink]] *\
                               (options.time_to_move + options.time_to_clean*vacuumed_at_node[source])

mdl.add(time_spent_cleaning < options.total_time_to_clean)

# -----------------------------------------------------------------------------
# Objective function
# -----------------------------------------------------------------------------
sum_vacumed = 0
for source in source_sink_arc_dict:
    if (source in charging_nodes):
        continue
    for sink in source_sink_arc_dict[source]:
        if (sink == charging_end_label):
            continue
        sum_vacumed += decision_Arcs[source_sink_arc_dict[source][sink]]*vacuumed_at_node[source]

for i in range(len(decision_dirt_minus)):
    sum_vacumed -= decision_dirt_plus[i]*(1/options.numScenarios)


mdl.add(mdl.maximize(sum_vacumed))


# -----------------------------------------------------------------------------
# Solve the Model
# -----------------------------------------------------------------------------
print("Solving model....")
msol = mdl.solve(TimeLimit = options.solverTimeLimit)

if msol:
    print('Solution Found')
    solution_arcs = []
    followed_arc_list = []
    sltn_d_plus_list = []
    sltn_d_minus_list = []
    followed_path_dict = {}    #will have key: source Value: sink

    for arcIndex in range(num_arcs):
        solution_arcs.append(msol[decision_Arcs[arcIndex]])
        #if the solution arc is selected
        if (solution_arcs[arcIndex] > 0):
            src_sink_tple = index_arc_dict[arcIndex]
            followed_arc_list.append(src_sink_tple)
            followed_path_dict[src_sink_tple[0]] = src_sink_tple[1]

    ordered_Path = dataPrep.orderedPathMaker(followed_path_dict, charging_nodes[0])

    for tple in followed_arc_list:
        if tple not in ordered_Path:
            print ('Arc Not in Start End Path : ', tple)

    if options.visualizePath:
        visualizer.visualizePath(dataPrep.data[0, :, :], ordered_Path, visualFrequency=1)

    if options.visualizeVacumed:
        visualizer.visualizeVacuumed(dataPrep.data[0, :, :], followed_path_dict)

    print(sum(solution_arcs))

    dirtVacumed = 0
    for i in range(len(decision_Arcs)):
        dirtVacumed += rate_dirt_pickup*msol[decision_Arcs[i]]

    for i in range(len(decision_dirt_plus)):
        sltn_d_plus_list.append(msol[decision_dirt_plus[i]])
        sltn_d_minus_list.append(msol[decision_dirt_minus[i]])

    print('Average Plan, ', str(options.average_plan_used))
    print('Constant Vacuuming, ', str(options.constant_vacuuming))
    print('Number of Scenarios, ', str(options.numScenarios))
    print('Number of Nodes Visited, ', len(followed_arc_list))
    print('Amount Vacumed,', dirtVacumed)
    print('Dirt Plus Sum, ', sum(sltn_d_plus_list))
    print('Dirt Minus Sum,', sum(sltn_d_minus_list))
    print('Total Time to Clean, ', options.total_time_to_clean)
    print('Time to Move, ', options.time_to_move)
    print('Time to Clean, ', options.time_to_clean)
    print('Roomba Dirt Capacity, ', options.roomba_dirt_capacity)
    print('Dirt File, ', options.dirtFile)
    print('Done')
else:
    print('No solution Found')
