import pandas as pd
import numpy as np
import scipy.stats as stats
from itertools import groupby
import pickle
import sim
from datetime import datetime

def load_data():
    file = open("exp_struc/110017437_best.pkl",'rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho_0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc, rho_0, all_decay

def label_age(row):
    if row['age'] < 13:
        return 'child'
    elif row['age'] < 18:
        return 'adolescent'
    return 'adult'

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
    new_list = [x for x in rt_list if str(x) != 'nan']
    return new_list

def divide_data_from_planets(data,trial_type,column_name):
    output_list = []
    land_indices = data.loc[data['trial_type'] == "land"].index.tolist()
    leave_indices = data.loc[data['last_trial_on_planet']==True].index.tolist()
    if len(land_indices) == len(leave_indices):
        pairs = [[land_indices[i],leave_indices[i]+1] for i in range(len(land_indices))]
    else:
        print("Issue splitting up the data in divide_data_from_planets")
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
    subsection_data = data.loc[data['last_trial_on_planet']==True]
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


def get_galaxy(true_planet):
    exp_struc, __,__ = load_data()
    neigh_order = flatten_list(flatten_list(exp_struc))
    # select the true planets actually experienced
    exp_neigh = [neigh_order[i] for i in true_planet]

    return exp_neigh

def get_preced_galaxy(true_planet):
    exp_struc, __,__ = load_data()
    exp_neigh = []
    begin_exp = 100
    curr_planet = -1
    for block in range(4): # loop thru blocks
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

def chunk_galaxies(flat_galaxy_list):
    groups=[]
    for _, g in groupby(flat_galaxy_list,  key=lambda x: x):
        groups.append(list(g))      # Store group iterator as a list
    return groups

def number_planet_in_galaxy(flat_galaxy_list):
    chunked_galaxy_list = chunk_galaxies(flat_galaxy_list)
    return [i for galaxy in chunked_galaxy_list for i in range(len(galaxy))]


def get_true_planet_num(raw_data):
    subsection_data = raw_data.loc[raw_data['last_trial_on_planet']==True]
    block_list = subsection_data['block_num'].tolist()
    block_list = list(map(int, block_list))

    true_planet = []
    for block in range(4):
        temp = np.array(range(block_list.count(block+1))) + 20*block
        true_planet.append(list(temp))

    flat_true_planet = [x for sublist in true_planet for x in sublist]
    return flat_true_planet

def chunk_galaxies(flat_galaxy_list):
    groups=[]
    for _, g in groupby(flat_galaxy_list,  key=lambda x: x):
        groups.append(list(g))      # Store group iterator as a list
    return groups

def number_planet_in_galaxy(flat_galaxy_list):
    chunked_galaxy_list = chunk_galaxies(flat_galaxy_list)
    return [i for galaxy in chunked_galaxy_list for i in range(len(galaxy))]

def calc_transition_probs(df,preced_planet,planet_num):
    temp = df.galaxy.iloc[:planet_num+1].reset_index()
    temp['preced_planet'] = temp.galaxy.shift(1)
    total = len(temp.query("preced_planet =="+str(preced_planet)))

    if total > 0:
        gal_poor = len(temp.query("preced_planet =="+str(preced_planet)+" & galaxy==0"))
        gal_neut = len(temp.query("preced_planet =="+str(preced_planet)+" & galaxy==1"))
        gal_rich = len(temp.query("preced_planet =="+str(preced_planet)+" & galaxy==2"))

    else:
        return np.nan, np.nan, np.nan

    return gal_poor/total, gal_neut/total, gal_rich/total

def get_transition_matrix(df,n_planets):
    poor_to_poor_all, poor_to_neut_all, poor_to_rich_all,neut_to_poor_all, neut_to_neut_all, neut_to_rich_all, rich_to_poor_all, rich_to_neut_all, rich_to_rich_all = ([] for i in range(9))

    for p in range(n_planets):
        poor_to_poor, poor_to_neut, poor_to_rich = calc_transition_probs(df,0,p)
        poor_to_poor_all.append(poor_to_poor)
        poor_to_neut_all.append(poor_to_neut)
        poor_to_rich_all.append(poor_to_rich)

        neut_to_poor, neut_to_neut, neut_to_rich = calc_transition_probs(df,1,p)
        neut_to_poor_all.append(neut_to_poor)
        neut_to_neut_all.append(neut_to_neut)
        neut_to_rich_all.append(neut_to_rich)

        rich_to_poor, rich_to_neut, rich_to_rich = calc_transition_probs(df,2,p)
        rich_to_poor_all.append(rich_to_poor)
        rich_to_neut_all.append(rich_to_neut)
        rich_to_rich_all.append(rich_to_rich)

    df['gal_0_trans_0'] = poor_to_poor_all
    df['gal_0_trans_1'] = poor_to_neut_all
    df['gal_0_trans_2'] = poor_to_rich_all

    df['gal_1_trans_0'] = neut_to_poor_all
    df['gal_1_trans_1'] = neut_to_neut_all
    df['gal_1_trans_2'] = neut_to_rich_all

    df['gal_2_trans_0'] = rich_to_poor_all
    df['gal_2_trans_1'] = rich_to_neut_all
    df['gal_2_trans_2'] = rich_to_rich_all


    return df


def clean_data_indiv(filename,sub_num):

    raw_data = pd.read_csv(filename)

    age = raw_data.age.iloc[2]

    gender = raw_data.gender.iloc[2]

    num_failures = int(raw_data.num_failures.dropna().reset_index().num_failures[0])

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

    galaxy = get_galaxy(true_planet)

    num_in_galaxy = number_planet_in_galaxy(galaxy)

    gal_0,gal_1,gal_2 = galaxy_encounter(galaxy)

    preced_gal = get_preced_galaxy(true_planet)

    opt_prt, gems_per_dig,opt_gems_per_dig, opptun_cost, leave_thresh = sim.get_indiv_sub_prt(true_planet,reward_list)

    opt_prt_om,__,__, __, __ = sim.get_indiv_sub_prt_omniscent(true_planet,reward_list)


    n_planets = len(prts)
    planet = range(n_planets)
    sub_num = [sub_num]*n_planets
    age = [age]*n_planets
    gender = [gender]*n_planets
    num_failures = [num_failures]*n_planets
    total_reward = [total_reward]*n_planets

    # to be filled with cleaned data
    clean_data = pd.DataFrame({'sub_num':sub_num,'age':age,'gender':gender,'num_failures':num_failures,'block':block_num,'planet':planet,'true_planet':true_planet,'prt':prts,'initial_reward':initial_reward,'leave_thresh':leave_thresh,'decay_list':decay_list,
                               'reward_list':reward_list,'total_reward':total_reward,'rt_list':rt_list,'avg_rt':avg_rt,'galaxy':galaxy,'num_in_gal':num_in_galaxy,'preced_gal':preced_gal,
                               'gal_0_encount':gal_0,'gal_1_encount':gal_1,'gal_2_encount':gal_2,'opt_prt':opt_prt,'opt_prt_om':opt_prt_om})

    return clean_data

def clean_data_group(filenames):

    # concatenate
    clean_data = pd.DataFrame(columns=['sub_num','age','gender','num_failures','block','planet','true_planet','prt','initial_reward','leave_thresh','decay_list',
                                       'reward_list','total_reward','rt_list', 'avg_rt','galaxy','num_in_gal','preced_gal','gal_0_encount','gal_1_encount','gal_2_encount','opt_prt','opt_prt_om'])

    for i,f in enumerate(filenames):
        try:
            clean_data = pd.concat([clean_data, clean_data_indiv(f, i)])
        except:
            print("ERROR in loading and cleaning the raw data file")
            print(f)
            continue

    # cleab data
    clean_data = clean_data[['sub_num','age','gender','num_failures','block','planet','true_planet','prt','initial_reward','leave_thresh','decay_list',
                             'reward_list','total_reward','rt_list','avg_rt','galaxy','num_in_gal','preced_gal','gal_0_encount','gal_1_encount','gal_2_encount','opt_prt','opt_prt_om']]

    # convert columns to dtype
    clean_data = clean_data.astype({'sub_num':'int','age':'float','num_failures':'int','block':'int','prt': 'int','initial_reward':'int','planet':'int','true_planet':'int','total_reward':'int','leave_thresh':'float64','opt_prt':'int','opt_prt_om':'int'})

    # add columns for comparison with MVT
    clean_data['prt_rel_mvt'] = clean_data['prt'] - clean_data['opt_prt']
    clean_data['prt_rel_om'] = clean_data['prt'] - clean_data['opt_prt_om']
    clean_data['age_group'] = clean_data.apply (lambda row: label_age(row), axis=1)

    return clean_data

def make_sub_rt_df(sub_num, df):
    sub_df = pd.DataFrame(columns=['sub_num','age','block','planet_num','true_planet','stay_num','stay?','galaxy','prior_galaxy','num_in_gal'])
    curr_sub = df.query("sub_num=="+str(sub_num)).reset_index()
    n_planet = max(curr_sub.planet) + 1

    for p in range(n_planet): # don't need to remove planets that are at the end of blocks because we're interested in within planet dynamics
        curr_planet = curr_sub.query("planet=="+str(p)).reset_index()
        age = curr_sub.age[0]

        curr_block = curr_planet.block[0]
        true_planet = curr_planet.true_planet[0]

        curr_galaxy = curr_planet.galaxy[0]
        curr_prior_galaxy = curr_planet.preced_gal[0]
        num_in_gal = curr_planet.num_in_gal[0]
        old_rt = curr_planet.rt_list[0]
        n_stay = len(old_rt)
        
        if n_stay == 0:
            rt = [np.nan]
            n_stay = 1
        else:
            rt = []
            for i in range(len(old_rt)):
                if old_rt[i] == 0:
                    rt.append(0.01)
                else:
                    rt.append(old_rt[i])
        tmp = pd.DataFrame({'sub_num':[sub_num]*n_stay,'age':[age]*n_stay, 
                        'block':[curr_block]*n_stay,'planet_num':[p]*n_stay,'true_planet':[true_planet]*n_stay,'stay_num':range(n_stay),'stay?':[1]*(n_stay-1) + [0],
                        'galaxy':[curr_galaxy]*n_stay,'prior_galaxy':[curr_prior_galaxy]*n_stay,'num_in_gal':[num_in_gal]*n_stay,
                       'rt':rt})
        sub_df = pd.concat([sub_df,tmp])

    sub_df['zlog_rt'] = stats.zscore(np.log(sub_df['rt']),nan_policy='omit')
    sub_df['planet_n_norm'] = stats.zscore(list(sub_df['planet_num']))

    return sub_df

def make_rt_df(subs, full_df):
    rt_df = pd.DataFrame(columns=['sub_num','age','block','planet_num','stay_num','stay?','galaxy','prior_galaxy','num_in_gal'])

    for sub in subs:
        sub_df = make_sub_rt_df(sub, full_df)
        rt_df = pd.concat([rt_df,sub_df])
    rt_df['age_group'] = rt_df.apply (lambda row: label_age(row), axis=1)
    return rt_df


def transform_data_for_modeling(df,save_output=False):
    n_subs = np.max(df.sub_num)

    all_sub_num = []
    all_age = []
    all_block = []
    all_true_planet = []
    all_planet = []
    all_galaxy = []
    all_stay_num = []
    all_reward = []
    all_rt = []
    all_planet_in_block = []
    for sub_num in range(n_subs+1):
        try:
            sub_data = df.query("sub_num=="+str(sub_num))
            age = sub_data.age.values[0]
            planet_total = 0

            for b in range(1,5):
                block_data = sub_data.query("block=="+str(b))
                block_planets = block_data.planet
                planet_in_block = 0
                for planet in block_planets[:-1]: # don't include the last planet because time on planet ends mid planet
                    planet_data = block_data.query("planet=="+str(planet))
                    planet_reward = planet_data.reset_index().reward_list[0]
                    planet_rt = planet_data.reset_index().rt_list[0]
                    true_planet = planet_data.reset_index().true_planet[0]
                    galaxy = planet_data.reset_index().galaxy[0]
                    stay_num = 0
                    for idx, reward in enumerate(planet_reward):
                        all_sub_num += [sub_num]
                        all_age += [age]
                        all_block += [b]
                        all_true_planet += [true_planet]
                        all_planet += [planet_total]
                        all_galaxy += [galaxy]
                        all_stay_num += [stay_num]
                        all_reward += [reward]
                        all_rt += [round(planet_rt[idx])]
                        all_planet_in_block += [planet_in_block]
                        stay_num += 1
                    planet_total += 1
                    planet_in_block += 1
        except:
            continue
    transformed_data = pd.DataFrame({'sub_num':all_sub_num,'age':all_age,'block':all_block,'true_planet':all_true_planet,
                        'planet':all_planet,'galaxy':all_galaxy,'stay_num':all_stay_num,'reward':all_reward,
                        'planet_in_block':all_planet_in_block, 'rt': all_rt})
    if save_output:
        date = datetime.now().strftime("%Y%m%d")
        transformed_data.to_csv("transformed_data/all_data_"+date+".csv")
    return 

def transform_data_for_linear_regression(subs, df, save_output=False):
    output_df = pd.DataFrame()
    # loop thru subjects
    for sub_num in subs:
        sub_df = pd.DataFrame()
        sub_data = df.query("sub_num==@sub_num")
        # loop thru planets 
        n_planets = len(np.unique(sub_data.planet))
        for planet in range(n_planets-1): # skip planet at ends --> interrupted 
            planet_data = sub_data.query("planet==@planet").reset_index()
            true_planet = planet_data.true_planet[0]
            
            age = planet_data.age[0]
            
            gender = planet_data.gender[0]
            
            curr_planet_type = planet_data.galaxy[0]
            
            block = planet_data.block[0]
            
            if (planet>0):
                last_planet_type = sub_data.query("planet==@planet-1").reset_index().galaxy[0]
            
                if (int(last_planet_type==curr_planet_type)):
                    switch = 'no_switch'
                else:
                    switch = 'switch'
            else:
                switch = 'no_switch'
            
            prt_rel_om = planet_data.prt_rel_om[0]
            
            prt = planet_data.prt[0]
            
            opt_prt_om = planet_data.opt_prt_om[0]
            
            num_in_gal = planet_data.num_in_gal[0]
            
            leave_thresh = planet_data.leave_thresh[0]
                    
            temp = pd.DataFrame({'sub_num':sub_num,'prt':prt,'prt_rel_om':prt_rel_om,'leave_thresh':leave_thresh,'opt_prt_om':opt_prt_om,'gender':gender,'age':age,'block':block,'galaxy':curr_planet_type,'switch':switch,'true_planet':true_planet,'planet_n':planet,'num_in_gal':num_in_gal},index=[0])
                    
            curr_planet_block = planet_data.block[0]
            nxt_planet_block = sub_data.query("planet==@planet+1").reset_index().block[0]
            if curr_planet_block==nxt_planet_block: # only include planets not at end of block (ended prematuely)
                sub_df = pd.concat([sub_df,temp])
        try:
            sub_df['planet_n_norm'] = stats.zscore(sub_df['planet_n'])
        except:
            print(sub_num)
        output_df = pd.concat([output_df,sub_df])
    output_df['galaxy']=output_df.galaxy.replace({0:'poor',1:'neutral',2:'rich'})
    output_df['agez'] = stats.zscore(output_df['age'],nan_policy='omit')
    output_df['age_group'] = output_df.apply (lambda row: label_age(row), axis=1)
    save_data = False
    if save_data:
        date = datetime.now().strftime("%Y%m%d")
        output_df.to_csv("transformed_data/linear_df_"+date+".csv")
    return output_df