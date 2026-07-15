import scipy.stats as stats
import numpy as np

##### Helper function for running the simulation ####
def get_mean_decay(galaxy):
    if galaxy == 0:
        return 0.2
    elif galaxy == 1:
        return 0.5
    elif galaxy == 2:
        return 0.8
    else:
        return np.nan
    
def sample_decay(galaxy):
    if galaxy == 0:
        return stats.beta.rvs(13,51)
    elif galaxy == 1:
        return stats.beta.rvs(50,50)
    elif galaxy == 2:
        return stats.beta.rvs(50,12)
    else:
        return np.nan

def get_indiv_sub_prt_omniscent(galaxies,reward_trajectories):
    total_treasure = 0
    total_time =5.5

    harvest_time = 3
    travel_time = 15.5
    iti = 1.5

    opt_prt = []
    gems_per_dig = []
    opt_gems_per_dig = []
    opptun_cost = []
    leave_thresh = []

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

            galaxy = galaxies[r]
            if ((d==0) & (galaxy==0)):
                estim_decay = 0.5
            else:
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
                    galaxy = galaxies[r]
                    sample = sample_decay(galaxy)
                    dig = sample*dig
                    estim_decay = get_mean_decay(galaxy)
                    pred_next_dig = estim_decay*dig

                    opt_tot_rew += dig
                    opt_tot_tim += (harvest_time + iti)
                    trial_opptun_cost = (opt_tot_rew/opt_tot_tim)*(harvest_time + iti)

                opt_prt.append(prt)
                opt_gems_per_dig.append(dig)
                first_below = False

        total_time += travel_time
    return opt_prt, gems_per_dig,opt_gems_per_dig,opptun_cost, leave_thresh
