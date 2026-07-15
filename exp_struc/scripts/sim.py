import scipy.stats as stats
import numpy as np
import data_combiner as dc
import pickle
##### Helper function for running the simulation ####

def load_data(seed):
    file = open("../pickled_exp_parms/blocks/"+str(seed)+"_3.pkl",'rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho_0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc, rho_0, all_decay


def flatten_list(list):
    new_list = [item for sublist in list for item in sublist]
    return new_list


def sim(reward_trajectories,exp_struc):
    total_treasure = 0
    late_treasure = 0
    total_time = 0.5
    max_block_time = 300

    harvest_time = 2
    travel_time = 13.5
    iti = 1.5

    k=[1]
    prts=[]
    blocks =[]
    galaxy_types=[]


    for block in range(6):
        t = 0
        planet = 0
        r = 0
        curr_block = flatten_list(exp_struc[block])
        while (t < max_block_time) & (planet < 20):
            curr_trajectory = reward_trajectories[block][planet]

            curr_dig = curr_trajectory[r]

            total_treasure += curr_dig
            if block > 1:
                late_treasure += curr_dig

            if r > 0:
                k.append(curr_trajectory[r]/curr_trajectory[r-1])
            if r > 44:
                curr_dig = 0

            v_stay = curr_dig*(sum(k)/len(k))
            v_leave = ((total_treasure/total_time)*(harvest_time+iti))

            p_stay = v_stay/(v_stay +v_leave)

            choice = stats.bernoulli(p_stay).rvs()

            if choice == 0:
                prts.append(r)
                blocks.append(block)
                galaxy_types.append(curr_block[planet])
                r=0
                planet += 1
                t += travel_time
                total_time += travel_time
            else:
                r+=1
                t += (harvest_time + iti)
                total_time += (harvest_time + iti)

    return total_treasure,prts,blocks,galaxy_types,late_treasure

def sim_learn_rate(reward_trajectories,exp_struc,alpha=0.2):
    total_treasure = 0
    late_treasure = 0

    total_time = 0.5
    max_block_time = 300

    harvest_time = 2
    travel_time = 13.5
    iti = 1.5

    k=[1]
    prts=[]
    blocks =[]
    galaxy_types=[]
    v_leave = 45

    for block in range(6):
        t = 0
        planet = 0
        r = 0
        curr_block = flatten_list(exp_struc[block])
        while (t < max_block_time) & (planet < 20):
            curr_trajectory = reward_trajectories[block][planet]

            curr_dig = curr_trajectory[r]

            total_treasure += curr_dig

            if block > 1:
                late_treasure += curr_dig

            if r > 0:
                k.append(curr_trajectory[r]/curr_trajectory[r-1])
                delta = curr_dig/(harvest_time + iti)
            else:
                delta = curr_dig/(travel_time)

            v_leave = v_leave + alpha*delta

            v_stay = curr_dig*(sum(k)/len(k))

            p_stay = v_stay/(v_stay +v_leave)

            choice = stats.bernoulli(p_stay).rvs()

            if choice == 0:
                prts.append(r)
                blocks.append(block)
                galaxy_types.append(curr_block[planet])
                r=0
                planet += 1
                t += travel_time
                total_time += travel_time
            else:
                r+=1
                t += (harvest_time + iti)
                total_time += (harvest_time + iti)

    return total_treasure,prts,blocks,galaxy_types, late_treasure

def get_indiv_sub_prt(seed,true_planet,reward_trajectories):
    exp_struc, rho_0, all_decay = load_data(seed)
    flat_decay = flatten_list(all_decay)

    total_treasure = 0
    total_time = 3.5

    harvest_time = 2
    travel_time = 8.5
    iti = 1.5

    opt_prt = []
    gems_per_dig = []
    opt_gems_per_dig = []
    opptun_cost = []
    leave_thresh = []

    k=[0.5]
    for r in range(len(reward_trajectories)): # loop thru planets
        #print("planet: " + str(r))
        curr_trajectory = reward_trajectories[r].copy()

        actual_prt = len(reward_trajectories[r])
        prt = 0
        first_below = True

        for d in range(actual_prt): # loop thru dig
            # if continued to dig
            prt += 1
            if d > 0:
                if curr_trajectory[d-1] == 0:
                    k.append(0)
                else:
                    k.append(curr_trajectory[d]/curr_trajectory[d-1])
                    #print('actual decay: ' + str(curr_trajectory[d]/curr_trajectory[d-1]))
                    curr_true_planet = true_planet[r]
                    #print('r :' + str(r))
                    #print('true planet: ' + str(curr_true_planet))
                    #print('stored decay: ' + str(flat_decay[curr_true_planet][d-1]))


            dig = curr_trajectory[d]
            #print('reward: ' + str(dig))
            total_treasure += dig
            total_time += (harvest_time + iti)

            estim_decay = sum(k)/len(k)
            #print('estim_decay: ' + str(estim_decay))
            pred_next_dig = estim_decay*dig

            overall_rr = (total_treasure/total_time)
            trial_opptun_cost = overall_rr*(harvest_time + iti)
            #print('overall_rr: '+str(total_treasure/total_time))


            # This is the point at which the forager left the patch
            if prt == actual_prt:
                thresh_estim = sum(curr_trajectory[d-1:d+1])/2 # average these two together
                leave_thresh.append(thresh_estim)
                gems_per_dig.append(dig)
                opptun_cost.append(trial_opptun_cost)

            # this would be the MVT optimal time to leave
            if pred_next_dig <= trial_opptun_cost:
                if first_below:
                    opt_prt.append(prt)
                    opt_gems_per_dig.append(dig)
                    first_below = False

            if (d == (actual_prt-1)) & (pred_next_dig > trial_opptun_cost)& first_below:# they underharvester
                opt_tot_rew = total_treasure
                opt_tot_tim = total_time
                while pred_next_dig > trial_opptun_cost:
                    prt += 1
                    curr_true_planet = true_planet[r]
                    sample = min(max(flat_decay[curr_true_planet][d-1],0),1)
                    dig = sample*dig
                    estim_decay = sum(k)/len(k)
                    pred_next_dig = estim_decay*dig

                    opt_tot_rew += dig
                    opt_tot_tim += (harvest_time + iti)
                    trial_opptun_cost = (opt_tot_rew/opt_tot_tim)*(harvest_time + iti)

                opt_prt.append(prt)
                opt_gems_per_dig.append(dig)
                first_below = False

        total_time = total_time + travel_time
    return opt_prt, gems_per_dig,opt_gems_per_dig,opptun_cost, leave_thresh

def get_mean_decay(galaxy):
    if galaxy == 0:
        return 0.2
    elif galaxy == 1:
        return 0.5
    elif galaxy == 2:
        return 0.8
    else:
        return np.nan

def get_indiv_sub_prt_omniscent(seed,true_planet,reward_trajectories):
    exp_struc, rho_0, all_decay = load_data(seed)
    flat_decay = flatten_list(all_decay)
    flat_exp_struc = flatten_list(flatten_list(exp_struc))

    total_treasure = 0
    total_time = 3.5

    harvest_time = 2
    travel_time = 8.5
    iti = 1.5

    opt_prt = []
    gems_per_dig = []
    opt_gems_per_dig = []
    opptun_cost = []
    leave_thresh = []

    k=[0.5]
    for r in range(len(reward_trajectories)): # loop thru planets
        curr_trajectory = reward_trajectories[r].copy()

        actual_prt = len(reward_trajectories[r])
        prt = 0
        first_below = True

        for d in range(actual_prt): # loop thru dig
            # if continued to dig
            prt += 1

            dig = curr_trajectory[d]
            total_treasure = total_treasure + dig
            total_time += (harvest_time + iti)

            galaxy = flat_exp_struc[true_planet[r]]
            estim_decay = get_mean_decay(galaxy)
            pred_next_dig = estim_decay*dig

            overall_rr = (total_treasure/total_time)
            trial_opptun_cost = overall_rr*(harvest_time + iti)


            # This is the point at which the forager left the patch
            if prt == actual_prt:
                thresh_estim = sum(curr_trajectory[d-1:d+1])/2 # average these two together
                leave_thresh.append(thresh_estim)
                gems_per_dig.append(dig)
                opptun_cost.append(trial_opptun_cost)

            # this would be the MVT optimal time to leave
            if pred_next_dig <= trial_opptun_cost:
                if first_below:
                    opt_prt.append(prt)
                    opt_gems_per_dig.append(dig)
                    first_below = False

            if (d == (actual_prt-1)) & (pred_next_dig > trial_opptun_cost)& first_below:# they underharvester
                opt_tot_rew = total_treasure
                opt_tot_tim = total_time
                while pred_next_dig > trial_opptun_cost:
                    prt += 1
                    curr_true_planet = true_planet[r]
                    sample = flat_decay[curr_true_planet][prt-1]
                    dig = sample*dig
                    estim_decay = sum(k)/len(k)
                    pred_next_dig = estim_decay*dig

                    opt_tot_rew += dig
                    opt_tot_tim += (harvest_time + iti)
                    trial_opptun_cost = (opt_tot_rew/opt_tot_tim)*(harvest_time + iti)

                opt_prt.append(prt)
                opt_gems_per_dig.append(dig)
                first_below = False

        total_time += travel_time
    return opt_prt, gems_per_dig,opt_gems_per_dig,opptun_cost, leave_thresh
