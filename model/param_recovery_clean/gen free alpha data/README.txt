run simulate_structLearning_softmax.jl to generate sim subjects with free alpha 

After running, two files will be generated (if not already there in data folder):
all_data_sim_alpha_free.csv
ref_point_data_planet_by_planet_sim.csv
Both are required.

num of subjects to sim and be defined inside this code. 

Use: extract_parameter_recovery.jl 
To extract inferred parameter vs ground truth - > combined into a csv for later recovery analysis