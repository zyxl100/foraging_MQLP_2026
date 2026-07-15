import numpy as np
import pandas as pd
import scipy.stats as stats
import pickle
import seaborn as sns
import random
import matplotlib.pyplot as plt
import os.path
import operator
from itertools import combinations
from random import randint
from datetime import datetime
import copy
import sim
import sim_crp
import sys
from collections import Counter


def flatten_list(list):
    new_list = [item for sublist in list for item in sublist]
    return new_list

def load_data(cond,seed):
    file = open('../pickled_exp_parms/condition_'+cond+'_'+str(seed)+'.pkl','rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc,rho0, all_decay

def get_counts(exp_struc):
    flat_struc = []
    pairs = []
    for block in range(5):
        flat_struc.append(flatten_list(exp_struc[block]))
        pairs.append([[flat_struc[block][i],flat_struc[block][i+1]] for i in range(16)])
    pairs = flatten_list(pairs)
    count = Counter(map(tuple, pairs))
    return count

def store_ratios(count):
    count_dict = {}
    # poor
    denom = (count[(0,0)] + count[(0,1)] + count[(0,2)])
    count_dict['poor_poor'] = count[(0,0)]/denom
    count_dict['poor_neutral'] = count[(0,1)]/denom
    count_dict['poor_rich'] = count[(0,2)]/denom

    # neutral
    denom = (count[(1,1)] + count[(1,0)] + count[(1,2)])
    count_dict['neutral_neutral'] = count[(1,1)]/denom
    count_dict['neutral_poor'] = count[(1,0)]/denom
    count_dict['neutral_rich'] = count[(1,2)]/denom

    # rich
    denom = (count[(2,2)] + count[(2,0)] + count[(2,1)])
    count_dict['rich_rich'] = count[(2,2)]/denom
    count_dict['rich_neutral'] = count[(2,1)]/denom
    count_dict['rich_poor'] = count[(2,0)]/denom

    return count_dict

def show_ratios(ratio_dict):
    print('poor to poor')
    print(ratio_dict['poor_poor'])

    print('poor to neutral')
    print(ratio_dict['poor_neutral'])

    print('poor to rich')
    print(ratio_dict['poor_rich'])


    print('neutral to neutral')
    print(ratio_dict['neutral_neutral'])

    print('neutral to poor')
    print(ratio_dict['neutral_poor'])

    print('neutral to rich')
    print(ratio_dict['neutral_rich'])


    print('rich to rich')
    print(ratio_dict['rich_rich'])

    print('rich to poor')
    print(ratio_dict['rich_poor'])

    print('rich to neutral')
    print(ratio_dict['rich_neutral'])
    print('')
    return


def load_data(seed):
    file = open('../pickled_exp_parms/blocks/'+str(seed)+'.pkl','rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc,rho0, all_decay

def load_mdp(seed):
    file = open('../pickled_exp_parms/mdp_'+str(seed)+'.pkl','rb')
    data= pickle.load(file)
    all_change_points = data[0]
    all_n_cp = data[1]
    all_next_galaxy = data[2]
    all_counter = data[3]
    file.close()
    return all_change_points, all_n_cp, all_next_galaxy, all_counter

def flatten_list(list):
    new_list = [item for sublist in list for item in sublist]
    return new_list

def make_crp_sub_df(seed,params,sub_num):
    alpha, prior_tau, hyper_mu, hyper_var = params

    num_particles = 50
    choices, all_reward_exp,true_planet = sim_crp.crp_samples(seed,params,num_particles,20)
    prts =  [sim_crp.get_prts(block) for block in choices]
    exp_struc, __,__ = load_data(seed)
    sub_df = pd.DataFrame(columns=['sub_num','alpha','prior_tau','hyper_mu','hyper_var','block','galaxy','prt'])
    for block in range(5):
        n_planets = len(prts[block])
        tmp = pd.DataFrame({'sub_num':[sub_num]*n_planets,
                            'alpha':[alpha]*n_planets,'prior_tau':[prior_tau]*n_planets,'hyper_mu':[hyper_mu]*n_planets,'hyper_var':[hyper_var]*n_planets,
                           'block':[block]*n_planets,'galaxy':flatten_list(exp_struc[block])[:n_planets],
                           'prt':prts[block]})
        sub_df = pd.concat([sub_df,tmp])

    sub_df['reward'] = all_reward_exp
    sub_df['true_planet'] = true_planet
    sub_df['opt_prt'],__,__,__,__ = sim.get_indiv_sub_prt(seed,true_planet,all_reward_exp)
    sub_df['opt_prt_om'],__,__,__,__ = sim.get_indiv_sub_prt_omniscent(seed,true_planet,all_reward_exp)

    return sub_df

def make_crp_df(seed,n_subs):
    sub_n = 0
    df = pd.DataFrame(columns=['sub_num','alpha','prior_tau','hyper_mu','hyper_var','block','galaxy','prt','reward','true_planet','opt_prt','opt_prt_om'])
    for sub in range(n_subs):
        alpha = 0.01#max(min(stats.norm.rvs(loc=0.01,scale=1,size=1)[0],10),0.001)
        prior_tau = 1
        hyper_mu = max(min(stats.norm.rvs(loc=0.99,scale=0.01,size=1)[0],1),0.001)
        #hyper_var = max(min(stats.norm.rvs(loc=0.003,scale=0.001,size=1)[0],1),0.001)
        hyper_var = max(min(stats.norm.rvs(loc=0.003,scale=0.001,size=1)[0],1),0.001)
        params = [alpha,prior_tau,hyper_mu,hyper_var]
        sub_df = make_crp_sub_df(seed,params,sub_n)
        df = pd.concat([df,sub_df])
        sub_n += 1
    return df


def make_bayes_sub_df(seed,params,sub_num):
    hyper_mu,hyper_var = params
    choices, all_reward_exp,true_planet = sim_crp.bayes_samples(seed,params,20)
    prts =  [sim_crp.get_prts(block) for block in choices]
    exp_struc, __,__ = load_data(seed)
    sub_df = pd.DataFrame(columns=['sub_num','hyper_mu','hyper_var','block','galaxy','prt'])
    for block in range(5):
        n_planets = len(prts[block])
        tmp = pd.DataFrame({'sub_num':[sub_num]*n_planets,
                            'hyper_mu':[hyper_mu]*n_planets,'hyper_var':[hyper_var]*n_planets,
                           'block':[block]*n_planets,'galaxy':flatten_list(exp_struc[block])[:n_planets],
                           'prt':prts[block]})
        sub_df = pd.concat([sub_df,tmp])
    sub_df['reward'] = all_reward_exp
    sub_df['true_planet'] = true_planet
    sub_df['opt_prt'],__,__,__,__ = sim.get_indiv_sub_prt(seed,true_planet,all_reward_exp)
    sub_df['opt_prt_om'],__,__,__,__ = sim.get_indiv_sub_prt_omniscent(seed,true_planet,all_reward_exp)

    return sub_df

def make_bayes_df(seed,n_subs):
    sub_n = 0
    df = pd.DataFrame(columns=['sub_num','hyper_mu','hyper_var','block','galaxy','prt','reward','true_planet','opt_prt','opt_prt_om'])
    for sub in range(n_subs):
        hyper_mu = max(min(stats.norm.rvs(loc=0.99,scale=0.01,size=1)[0],1),0.001)
        hyper_var = max(min(stats.norm.rvs(loc=0.0625,scale=0.01,size=1)[0],1),0.01)
        params = [hyper_mu,hyper_var]
        sub_df = make_bayes_sub_df(seed,params,sub_n)
        df = pd.concat([df,sub_df])
        sub_n += 1
    return df

def run_sims(seed,n_sim=50):
    crp_df = make_crp_df(seed,n_sim)
    bayes_df = make_bayes_df(seed,n_sim)

    crp_df['prt_rel_mvt'] = crp_df['prt'] - crp_df['opt_prt']
    crp_df['prt_rel_mvt_om'] = crp_df['prt'] - crp_df['opt_prt_om']
    crp_df = crp_df.astype({'galaxy':'int','prt_rel_mvt':'int','prt_rel_mvt_om':'int'})

    bayes_df['prt_rel_mvt'] = bayes_df['prt'] - bayes_df['opt_prt']
    bayes_df['prt_rel_mvt_om'] = bayes_df['prt'] - bayes_df['opt_prt_om']
    bayes_df = bayes_df.astype({'galaxy':'int','prt_rel_mvt':'int','prt_rel_mvt_om':'int'})

    return crp_df, bayes_df


def model_difference(crp_df, bayes_df):
    crp_sub_avg = crp_df.groupby(['sub_num']).prt_rel_mvt_om.mean().reset_index()

    bayes_sub_avg = bayes_df.groupby(['sub_num']).prt_rel_mvt_om.mean().reset_index()

    crp=crp_sub_avg.prt_rel_mvt_om.mean()
    bayes=bayes_sub_avg.prt_rel_mvt_om.mean()

    print(abs(crp-bayes))

    return abs(crp-bayes)


def save_to_files(seed,difference):
    with open('../pickled_exp_parms/mdp_eval/difference_'+str(seed)+'.pkl', 'wb') as f_out:
         pickle.dump([difference],f_out)
    return

def main():
    seed = int(sys.argv[1])
    crp_df, bayes_df = run_sims(seed)
    difference =  model_difference(crp_df, bayes_df)
    save_to_files(seed,difference)


def main_old():
    seed = int(sys.argv[1])
    all_conds = ['poor_graded','poor_extreme','rich_graded','rich_extreme']

    for cond in all_conds:
        print(cond)
        exp_struc, __, __ = load_data(cond,seed)
        count = get_counts(exp_struc)
        count_dict = store_ratios(count)
        show_ratios(count_dict)


if __name__ == "__main__":
    main()
