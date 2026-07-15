import numpy as np
import scipy.stats as stats
from collections import Counter
import pickle
import sys


def pickle_mdp(seed,all_change_points,all_n_cp,all_next_galaxy,all_counter):
    with open('../pickled_exp_parms/mdps/'+str(seed)+'.pkl', 'wb') as f_out:
            pickle.dump([all_change_points,all_n_cp,all_next_galaxy,all_counter],f_out)

def make_mdp(seed):
    # set random seed
    print(seed)
    np.random.seed(seed=seed)
    n_planets = 20
    all_change_points= {}
    all_n_cp = {}
    all_next_galaxy = {}
    all_counter = {}


    for block in range(5):
        #print("BLOCK: " + str(block))
        #change_points = stats.binom.rvs(1,0.2,size= n_planets-1) # if 1 then switch galaxies
        change_points = stats.binom.rvs(1,0.2,size= n_planets-1) # if 1 then switch galaxies
        n_cp = sum(change_points)
        next_galaxy = stats.binom.rvs(1,0.5,size= n_cp)
        #if block < 2:
            #while (change_points[0] == 1) | (change_points[1] == 1): # make sure don't have super short galaxies at beginning
                #change_points = stats.binom.rvs(1,0.5,size= n_planets) # if 1 then switch galaxies
                #n_cp = sum(change_points)
                #next_galaxy = stats.binom.rvs(1,0.5,size= n_cp)
        #else:
            #while ((np.mean(change_points[:16]) > 0.55) | (np.mean(change_points[:16]) < 0.45)) | ((np.mean(next_galaxy[:16]) > 0.55) | (np.mean(next_galaxy[:16]) < 0.45)) :
                #change_points = stats.binom.rvs(1,0.5,size= n_planets) # if 1 then switch galaxies
                #n_cp = sum(change_points)
                #next_galaxy = stats.binom.rvs(1,0.5,size= n_cp)


        galaxy_assign = np.insert(np.cumsum(change_points),0,0)
        c = Counter(galaxy_assign)

        all_change_points[block] = change_points
        all_n_cp[block] = n_cp
        all_next_galaxy[block] = next_galaxy
        all_counter[block] = list(c.values())


    #print('change_points')
    #print(change_points)
    #print('cumsum')
    #print(galaxy_assign)
    #print('values')
    #print(c.values())
    #print(np.cumsum(change_points))
    #print('# change_points : '+str(n_cp))
    #print('next_galaxy')
    #print(next_galaxy)

    return all_change_points,all_n_cp,all_next_galaxy,all_counter


def main():
    seed = int(sys.argv[1])
    all_change_points,all_n_cp,all_next_galaxy,all_counter = make_mdp(seed)
    pickle_mdp(seed,all_change_points,all_n_cp,all_next_galaxy,all_counter)


if __name__ == "__main__":
    main()
