import pandas as pd
import numpy as np
from itertools import groupby
import pickle
import sim


def load_data(cond):
    file = open("../pickled_exp_parms/condition_"+cond+".pkl",'rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho_0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc, rho_0, all_decay

### helper functions for making the large dataframe ###
def flatten_list(list):
    new_list = [item for sublist in list for item in sublist]
    return new_list

def get_last_planet_in_block(sub_data):
    num_planets = []
    block_list=list(sub_data['block'])
    for i in range(1,7):
        num_planets.append(block_list.count(i))
    return num_planets

def drop_nan_rt(rt_list):
    # Max rt in milliseconds
    new_list = [x for x in rt_list if str(x) != 'nan']

    return new_list

def divide_data_from_planets(data,trial_type,column_name):
    output_list = []
    land_indices = data.loc[data['trial_type'] == "land"].index.tolist()
    leave_indices = data.loc[data['last_trial_on_planet']=="TRUE"].index.tolist()
    if len(land_indices) == len(leave_indices):
        pairs = [[land_indices[i],leave_indices[i]+1] for i in range(len(land_indices))]
    else:
        print("noooo")

    for p in pairs:
        sub_section = data.iloc[p[0]:p[1],:]

        type_trials = sub_section.loc[sub_section["trial_type"]==trial_type]
        value= type_trials[column_name]

        new_list = [float(i) for i in value.tolist()]

        output_list.append(new_list)

    return output_list

def get_initial_reward(data):
    land_trials = data.loc[data['trial_type'] == 'land']
    initial_reward = land_trials["next_reward"]

    return initial_reward


def get_prts(data):
    subsection_data = data.loc[data['last_trial_on_planet']=="TRUE"]
    prt = subsection_data['prt'].tolist()
    block = subsection_data['block_num'].tolist()
    prt = [int(i) + 1 for i in prt]


    return prt,block

def get_leave_thresh(data):
    rewards = divide_data_from_planets(data,"harvest","reward_received")

    reward_thresh = [planet[-1] for planet in rewards] # get the last reward received on this planet

    return reward_thresh

def get_decay_thresh(data):

    decay_list = divide_data_from_planets(data,"harvest","decay_rate_exp")

    decay_thresh = [d[-1] for d in decay_list]

    decay_leading = []


    decay_leading = [sum(d[:-1])/len(d[:-1]) if len(d[:-1]) > 0 else d[-1] for d in decay_list]

    return decay_thresh,decay_leading

def get_rt_thresh(rt_list):

    avg_rt = [sum(r)/len(r) for r in rt_list]

    rt_thresh =[r[-1] for r in rt_list]

    rt_rest = [r[:-1] for r in rt_list]
    rt_leading = [sum(r[:-1])/len(r[:-1]) if len(r[:-1]) > 0 else r[-1] for r in rt_list]

    return avg_rt,rt_thresh, rt_leading, rt_rest

def calc_avg_reward_rate(data,len_exp=600):
    # get reward rate per seconds, exp is 10 min so 600 sec long
    rr = np.nansum(data["reward_received"])/len_exp

    return rr

def catch_trial_perf(data):

    catch_trials = data.loc[data['trial_type']=="catch"]

    num_correct = sum(catch_trials["key_press"] == 90)

    rt = catch_trials["rt"].mean()

    return num_correct, rt


def get_galaxy(data,true_planet):
    condition = int(data['condition'][1])
    exp_struc, __,__ = load_data(condition)
    neigh_order = flatten_list(flatten_list(exp_struc))
    # select the true planets actually experienced
    exp_neigh = [neigh_order[i] for i in true_planet]

    return exp_neigh

def get_preced_galaxy(data,true_planet):
    condition = int(data['condition'][1])
    exp_struc, __,__ = load_data(condition)
    exp_neigh = []
    begin_exp = 100
    curr_planet = -1
    for block in range(6): # loop thru blocks
        curr_block = exp_struc[block]
        for g in range(len(curr_block)): # loop thru galaxies
            curr_galaxy = curr_block[g]
            if g > 0:
                prev_galaxy_type = curr_block[g-1][0] # look at last galaxy
            else:
                if block == 0:
                    prev_galaxy_type = begin_exp
                else:
                    prev_galaxy_type = end_block_gal_type  # go to the last block, what galaxy type did we leave off at
            for planet in range(len(curr_galaxy)):
                curr_planet += 1
                if curr_planet in true_planet: # they visited this planet
                    end_block_gal_type = curr_block[g][planet]
                    exp_neigh.append(prev_galaxy_type)
    return exp_neigh

def get_prev_galaxies(galaxy_data):
    sub_gal_grouped = [list(j) for i, j in groupby(galaxy_data)]
    sub_gal_order = [x[0] for x in sub_gal_grouped]

    gal_prev_1 = [100] +sub_gal_order[:-1]
    gal_prev_2 = [100,100] +sub_gal_order[:-2]
    gal_prev_3 = [100,100,100] +sub_gal_order[:-3]

    prev_1 = []
    prev_2 = []
    prev_3 = []
    for g in range(len(sub_gal_grouped)):
        for planet in range(len(sub_gal_grouped[g])):
            prev_1.append(gal_prev_1[g])
            prev_2.append(gal_prev_2[g])
            prev_3.append(gal_prev_3[g])
    return prev_1, prev_2, prev_3

def galaxy_encounter(galaxy_data):
    gal_0= np.cumsum(np.where(np.array(galaxy_data)==0,1,0))
    gal_1= np.cumsum(np.where(np.array(galaxy_data)==1,1,0))
    gal_2= np.cumsum(np.where(np.array(galaxy_data)==2,1,0))

    return gal_0, gal_1, gal_2

def get_true_planet_num(raw_data):
    subsection_data = raw_data.loc[raw_data['last_trial_on_planet']=="TRUE"]
    block_list = subsection_data['block_num'].tolist()
    block_list = list(map(int, block_list))

    true_planet = []
    for block in range(6):
        temp = np.array(range(block_list.count(block+1))) + 20*block
        true_planet.append(list(temp))

    flat_true_planet = [x for sublist in true_planet for x in sublist]
    return flat_true_planet

def clean_data_indiv(filename,sub_num):
    print(sub_num)

    raw_data = pd.read_csv(filename)

    age = int(raw_data.query("trial_type=='demo'").responses.tolist()[0].split(":")[1])

    gender = raw_data.query("trial_type=='demo'").planet.tolist()[0].split(":")[1]

    condition = raw_data['condition'][1]

    prts,block_num = get_prts(raw_data)

    true_planet = get_true_planet_num(raw_data)

    initial_reward = get_initial_reward(raw_data)

    leave_thresh = get_leave_thresh(raw_data)

    decay_list = divide_data_from_planets(raw_data,"harvest","decay_rate_exp")

    reward_list = divide_data_from_planets(raw_data,"harvest","reward_received")

    total_reward = sum([sum(lst) for lst in reward_list[:-1]])

    rt_list = divide_data_from_planets(raw_data,"decision","rt")

    avg_rt = [np.mean(x) for x in rt_list]

    rt_list = [drop_nan_rt(i) for i in rt_list]

    catch_perf, catch_rt = catch_trial_perf(raw_data)

    galaxy = get_galaxy(raw_data,true_planet)

    prev_1,prev_2,prev_3 = get_prev_galaxies(galaxy)

    gal_0,gal_1,gal_2 = galaxy_encounter(galaxy)

    preced_gal = get_preced_galaxy(raw_data,true_planet)

    opt_prt, gems_per_dig,opt_gems_per_dig, opptun_cost, leave_thresh = sim.get_indiv_sub_prt(reward_trajectories=reward_list)


    n_planets = len(prts)
    planet = range(n_planets)
    sub_num = [sub_num]*n_planets
    catch_perf = [catch_perf]*n_planets
    catch_rt = [catch_rt]*n_planets
    total_reward = [total_reward]*n_planets
    condition = [condition]*n_planets
    age = [age]*n_planets
    gender = [gender]*n_planets
    # to be filled with cleaned data
    clean_data = pd.DataFrame({'sub_num':sub_num,'condition':condition,'age':age,'gender':gender,'block':block_num,'planet':planet,'true_planet':true_planet,'prt':prts,'initial_reward':initial_reward,'leave_thresh':leave_thresh,'decay_list':decay_list,
                               'reward_list':reward_list,'total_reward':total_reward,'rt_list':rt_list,'avg_rt':avg_rt,'catch_perf':catch_perf,'catch_rt':catch_rt,'galaxy':galaxy,'preced_gal':preced_gal,'prev_1':prev_1,'prev_2':prev_2,'prev_3':prev_3,
                               'gal_0_encount':gal_0,'gal_1_encount':gal_1,'gal_2_encount':gal_2,'opt_prt':opt_prt})

    return clean_data

def clean_data_group(filenames):

    # concatenate
    clean_data = pd.DataFrame(columns=['sub_num','condition','age','gender','block','planet','true_planet','prt','initial_reward','leave_thresh','decay_list',
                                       'reward_list','total_reward','rt_list', 'avg_rt','catch_perf','catch_rt','galaxy','preced_gal','prev_1','prev_2','prev_3',
                                      'gal_0_encount','gal_1_encount','gal_2_encount','opt_prt'])

    for i,f in enumerate(filenames):
        clean_data = clean_data.append(clean_data_indiv(f,i))
    # cleab data
    clean_data = clean_data[['sub_num','condition','age','gender','block','planet','true_planet','prt','initial_reward','leave_thresh','decay_list',
                             'reward_list','total_reward','rt_list','avg_rt','catch_perf','catch_rt','galaxy','preced_gal','prev_1','prev_2','prev_3',
                             'gal_0_encount','gal_1_encount','gal_2_encount','opt_prt']]

    # convert columns to dtype
    clean_data = clean_data.astype({'sub_num':'int','age':'int','block':'int','condition':'int','prt': 'int','initial_reward':'int','planet':'int','true_planet':'int','total_reward':'int','catch_perf':'int','leave_thresh':'float64',
                                   'opt_prt':'int'})

    return clean_data
