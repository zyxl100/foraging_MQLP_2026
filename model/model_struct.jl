struct Experiment
    n_blocks
    block_max_time
    block_n_planet
    harvest_time
    travel_time
    alien_time
    iti
end

# mutable struct Behavior
#     true_planet
#     prt
#     galaxy
#     reward_list
# end

struct Behavior
    true_planet
    galaxy
    prt
    reward_list
    p_stay_list     # ADD THIS
    choice_list     # ADD THIS
end


mutable struct Block_Tracker
    block_time
    planet
end

mutable struct Planet_Tracker
    on_planet
    galaxy
    curr_reward
    prt
    true_planet
    reward_list
    decay_list
end
