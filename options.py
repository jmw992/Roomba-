total_time_to_clean = 100
time_to_move = 1
time_to_clean = 2
roomba_dirt_capacity = 60
numScenarios = 10

# dirtFile = "data/master_data.npy"
# dirtFile = 'data/2by2_10scenarios.npy'
# dirtFile = 'data/3by3_10scenarios.npy'
# dirtFile = 'data/4by4toy_10scenarios.npy'
# dirtFile = 'data/5by5floor10scenarios.npy'
# dirtFile = 'data/6by6floor10scenarios.npy'
dirtFile = 'data/7by7floor10scenarios.npy'
# dirtFile = 'data/9by9_10scenarios.npy'
# dirtFile = 'data/small_floor10scenarios.npy'

subTourFile = dirtFile[:-4]
subTourFile = subTourFile[5:]

charging_start_value = -2
charging_end_label = 900

average_plan_used = False
constant_vacuuming = True
visualizePath = False
visualizeVacumed = True

solverTimeLimit = 300

if average_plan_used == True:
    numScenarios = 1