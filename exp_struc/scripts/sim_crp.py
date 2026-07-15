import numpy as np
import scipy.stats as stats
import pandas as pd
import random
import pickle
import particle_filter as pf
import sys
from more_itertools import split_after
from datetime import datetime

def condition_type(cond):
    if cond == 1:
        condition = "poor_extreme"
    elif cond == 2:
        condition = "poor_graded"
    elif cond == 3:
        condition = "neutral_graded"
    elif cond == 4:
        condition = "neutral_extreme"
    elif cond == 5:
        condition = "rich_graded"
    elif cond == 6:
        condition = "rich_extreme"
    return condition

def load_data_old(cond,seed):
    file = open('../pickled_exp_parms/condition_'+cond+'_'+str(seed)+'.pkl','rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc,rho0, all_decay

def load_data(seed):
    file = open('../pickled_exp_parms/blocks/'+str(seed)+'_3.pkl','rb')
    data= pickle.load(file)
    exp_struc = data[0]
    rho0 = data[1]
    all_decay = data[2]
    file.close()
    return exp_struc,rho0, all_decay

def get_sub_condition(all_data,sub_num):
    return all_data.query("sub_num=="+str(sub_num)).condition.tolist()[0]


def make_choice(prob_stay,curr_r):
    rand_num =  random.uniform(0, 1)
    if rand_num <= prob_stay:
        on_planet = True
        choice = 0
        curr_r += 1
    else:
        on_planet = False
        choice = 1
        curr_r = 0
    return choice, on_planet, curr_r

def soft_transform(param,lb,ub):
    """Transform so the param (fit w/o bounds) can be constrained within these bounds """
    bounded_param = lb + ((ub-lb)*(1/(1+np.exp(-param))))

    return bounded_param

def get_bins(max_reward,decay_rate):
    reward = max_reward
    bins=[max_reward]
    while reward > 4:
        reward = round(reward*decay_rate)
        bins = [reward] + bins
    return bins

def sampling_weights(memories):
    """Bias towards sampling more extreme events"""
    p_x = [1/len(memories) for i in memories] # uniform probability
    w_x = [abs(i-np.mean(memories)) for i in memories] # weights based on extremeness
    sampling_weights = np.array(w_x)*np.array(p_x)
    sampling_weights = sampling_weights/np.sum(sampling_weights) # normalize
    return sampling_weights

def sample_value(mu,var,num_samples):
    sample_v = stats.norm.rvs(loc=mu,scale=var**(1/2),size=1000)
    w = sampling_weights(sample_v)
    index = np.random.choice(1000,num_samples,p=w)
    v_samples = [sample_v[i] for i in index]
    pred_v = np.mean(v_samples)
    return pred_v

def square(x):
    return x*x

def square_root(x):
    return x**(1/2)

def infer_cluster(state,post):
    norm_post = pf.normalize(post+0.0000000001)
    #print('norm_post')
    #print(norm_post[0,:])
    cluster_mu = state["cluster_parameters"]["mean"]
    #print('cluster_mu')
    #print(cluster_mu[0,:])
    cluster_var = state["cluster_parameters"]["variance"]
    num_particles = state["num_particles"]

    # https://stats.stackexchange.com/questions/445231/compute-mean-and-variance-of-mixture-of-gaussians-given-mean-variance-of-compone
    mixture_mu = (np.inner(norm_post.flatten(),cluster_mu.flatten()))/num_particles
    expec_mix_square = (np.inner(norm_post.flatten(),(cluster_var.flatten() + (cluster_mu.flatten()**2))))/num_particles
    mixture_var = expec_mix_square - mixture_mu**2

    return mixture_mu,mixture_var

def expectation(state,post):
    v_mu = post*state["cluster_parameters"]["mean"]
    v_mu = np.sum(v_mu,axis=1) # sum across clusters
    v_mu = np.mean(v_mu,axis=0) # now take the mean overt partticles
    return v_mu

def mean_square_error(data):
    mu = np.mean(data)
    square_error = []

    for d in data:
        square_error.append((d-mu)**2)
    return sum(square_error)

def prior_update(prior_mu,prior_var,prior_tau,prior_n,data):
    n = 1
    mse= 0
    posterior_mu = (prior_n*prior_mu + n*data)/(prior_n + n)
    posterior_n = prior_n + n
    posterior_tau = prior_tau + n
    posterior_tau_var = prior_tau*prior_var +  mse + ((prior_n*n)/(prior_n +n))*((prior_mu - data)**2)
    posterior_var = posterior_tau_var/posterior_tau

    return posterior_mu, posterior_var, posterior_tau, posterior_n


def solve(m1,m2,std1,std2):
  a = 1/(2*std1**2) - 1/(2*std2**2)
  b = m2/(std2**2) - m1/(std1**2)
  c = m1**2 /(2*std1**2) - m2**2 / (2*std2**2) - np.log(std2/std1)
  return np.roots([a,b,c])

def auc(mu_1,var_1,mu_2,var_2):
  # https://stackoverflow.com/questions/32551610/overlapping-probability-of-two-normal-distribution-with-scipy
  #Get point of intersect
  result = solve(mu_1,mu_2,var_1**(1/2),var_2**(1/2))
  r = result[0]
  # integrate
  area = stats.norm.cdf(r,mu_2,var_2**(1/2)) + (1.-stats.norm.cdf(r,mu_1,var_1**(1/2)))
  return area

def get_prob_random_var(mu_1,var_1,mu_2,var_2):
  # https://stats.stackexchange.com/questions/50501/probability-of-one-random-variable-being-greater-than-another
  #p(x>y)
  # p(x-y) > 0
  # d = x-y
  expec_d = mu_1 - mu_2
  var_d = var_1 + var_2
  return 1- stats.norm.cdf((0-expec_d)/square_root(var_d))


def sample_from_dist_norm(mu,var,n_samples):
  samples = np.clip(stats.norm.rvs(loc=mu,scale=var**(1/2),size=n_samples),0,1)

  return np.mean(samples)

def sample_from_dist_gamma(alpha,beta,n_samples):
  samples = stats.gamma.rvs(a=alpha,scale=1/beta,size=n_samples)

  return np.mean(samples)


def get_decay(rewards_received,r):
    if rewards_received[r-1] == 0:
       actual_decay = 0
    else:
       actual_decay = rewards_received[r]/rewards_received[r-1]
    return actual_decay

def time_constant(planet,r,harvest_time,iti,travel_time):
    if r == 0:
        if planet == 0:
            tau = 5.5 + harvest_time+iti
        else:
            tau = travel_time+harvest_time+iti
    else:
        tau = harvest_time+iti
    return tau


def initialize_env_mvt():
    init_rho = 28
    rho = [init_rho] # estimate environment reward rate
    k = [1]# initialize to no decay, will keep a running average of this

    choices = []
    all_reward_exp = [] # reward list of the simulation
    true_planet = []


    n_blocks = 5
    block_max = 300

    return rho, k, choices, all_reward_exp,true_planet, n_blocks, block_max

def initialize_env_td(gamma):
    rho_init = 28/(1-gamma)

    q_val_bins = get_bins(135,0.9)
    q_val_bins.insert(0,0)
    num_states = len(q_val_bins) + 1
    q_vals_stay = np.ones(num_states)*rho_init # states are represented by the reward you just received, the value of staying is state dependent while the value of exiting is not
    q_exit = rho_init  # q-value for exiting is the same regardless of state

    choices = []
    all_reward_exp = [] # reward list of the simulation
    true_planet = []
    n_blocks = 5
    block_max = 300

    return q_val_bins, q_vals_stay,q_exit,choices, all_reward_exp, true_planet, n_blocks, block_max


def initialize_block():
    block_time = 0
    planet = 0
    prt = 0
    block_choice = []
    return block_time, planet, prt, block_choice

def initialize_planet(rho_0,block,planet_num,true_planet):
    reward_exp = []
    planet_decay = []
    on_planet = True
    reward = rho_0[block][planet_num]
    true_planet.append(block*20 +planet_num)
    return reward_exp, on_planet, reward, true_planet, planet_decay

def update_decay_list(k,all_decay,block,planet,prt):
    if prt > 0:
        k.append(all_decay[block][planet][prt-1])
    return k
######## MODELS #############################################################
def crp(seed,params,num_particles,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    alpha, prior_tau, hyper_mu, hyper_var = params

    state = pf.initial_state(num_particles,alpha,prior_tau,hyper_mu=hyper_mu,hyper_var=hyper_var)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)

                if prt > 0:
                    expec_decay_mu, expec_decay_var = infer_cluster(state,pf.normalize(post+eps))
                else:
                    expec_decay_mu, expec_decay_var = infer_cluster(state,pf.normalize(pf.prior(state)+eps))
                #print('decay_mu: ' + str(expec_decay_mu))
                #print('decay_var: ' + str(expec_decay_var))
                v_stay_mu = expec_decay_mu*reward
                v_stay_var = expec_decay_var*(reward**2)
                #print('v_stay_mu: ' + str(v_stay_mu))
                #print('v_stay_var: ' + str(v_stay_var))

                v_leave_mu = (total_reward/total_time)*(harvest_time+iti)
                v_leave_var =(total_reward/(total_time**2))*((harvest_time+iti)**2)
                #print('v_leave_mu: ' + str(v_leave_mu))
                #print('v_leave_var: ' + str(v_leave_var))

                prob_stay = get_prob_random_var(v_stay_mu,v_stay_var,v_leave_mu,v_leave_var)
                #print('prob stay: ' +str(prob_stay))

                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet


def crp_samples(seed,params,num_particles,n_samples,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    alpha, prior_tau, hyper_mu, hyper_var = params


    state = pf.initial_state(num_particles,alpha,prior_tau,hyper_mu=hyper_mu,hyper_var=hyper_var)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)

                    pf.resample_and_update_particles(state,post,[actual_decay])


                    #print('actual decay: ' + str(actual_decay))
                    #print('post')
                    #print(pf.normalize(post+eps)[0,:])

                #print('posterior')
                #print(pf.normalize(post+eps))
                if prt > 0:
                    expec_decay_mu, expec_decay_var = infer_cluster(state,post)
                else:
                    expec_decay_mu, expec_decay_var = infer_cluster(state,pf.prior(state))
                #print('decay_mu: ' + str(expec_decay_mu))
                #print('decay_var: ' + str(expec_decay_var))

                stay_samples = sample_from_dist_norm(expec_decay_mu,expec_decay_var,n_samples)
                stay_samples = stay_samples*reward
                leave_samples = sample_from_dist_gamma(total_reward,total_time,n_samples)
                leave_samples = leave_samples*(harvest_time+iti)

                #print('v_stay: ' + str(stay_samples))
                #print('v_leave: ' + str(leave_samples))

                if stay_samples > leave_samples:
                    prob_stay = 1
                else:
                    prob_stay = 0
                #print('prob stay: ' +str(prob_stay))


                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,[actual_decay])
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet


def crp_beta(seed,params,num_particles,beta,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    alpha, prior_tau, hyper_mu, hyper_var = params


    state = pf.initial_state(num_particles,alpha,prior_tau,hyper_mu=hyper_mu,hyper_var=hyper_var)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)

                expec_decay_mu, expec_decay_var = infer_cluster(state,pf.normalize(post+eps))

                v_stay_mu = expec_decay_mu*reward
                v_stay_var = expec_decay_var*(reward**2)


                v_leave_mu = (total_reward/total_time)*(harvest_time+iti)
                v_leave_var =(total_reward/(total_time**2))*((harvest_time+iti)**2)


                prob_stay = 1/(1+np.exp(-beta*0.01*(v_stay_mu - v_leave_mu)))

                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet

def bayes(seed,params,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    prior_mu = params[0]
    prior_var = params[1]
    prior_tau = 1
    prior_n = 0

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    prior_mu, prior_var, prior_tau, prior_n = prior_update(prior_mu,prior_var,prior_tau,prior_n,actual_decay)

                v_stay_mu = prior_mu*reward
                v_stay_var = prior_var*(reward**2)

                v_leave_mu = (total_reward/total_time)*(harvest_time+iti)
                v_leave_var =(total_reward/(total_time**2))*((harvest_time+iti)**2)

                prob_stay = get_prob_random_var(v_stay_mu,v_stay_var,v_leave_mu,v_leave_var)

                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet


def bayes_samples(seed,params,n_samples,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    prior_mu = params[0]
    prior_var = params[1]
    prior_tau = 1
    prior_n = 0

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    prior_mu, prior_var, prior_tau, prior_n = prior_update(prior_mu,prior_var,prior_tau,prior_n,actual_decay)

                stay_samples = sample_from_dist_norm(prior_mu,prior_var,n_samples)
                stay_samples = stay_samples*reward
                leave_samples = sample_from_dist_gamma(total_reward,total_time,n_samples)
                leave_samples = leave_samples*(harvest_time+iti)

                if stay_samples > leave_samples:
                    prob_stay = 1
                else:
                    prob_stay = 0

                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet


def bayes_beta(seed,params,beta,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    print(params)
    #condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(seed)

    prior_mu = params[0]
    prior_var = params[1]
    prior_tau = 1
    prior_n = 0

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 3.5

    planet = 0
    true_planet = []

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = min(max(all_decay[block][planet][prt-1],0),1)
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    prior_mu, prior_var, prior_tau, prior_n = prior_update(prior_mu,prior_var,prior_tau,prior_n,actual_decay)

                v_stay_mu = prior_mu*reward
                v_stay_var = prior_var*(reward**2)

                v_leave_mu = (total_reward/total_time)*(harvest_time+iti)
                v_leave_var =(total_reward/(total_time**2))*((harvest_time+iti)**2)

                prob_stay = 1/(1+np.exp(-beta*0.010*(v_stay_mu - v_leave_mu)))


                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*max(min(all_decay[block][planet][prt-1],1),0)

            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp,true_planet

def crp_mvt(params,cond_num,num_particles,harvest_time=2,iti=1.5,travel_time=8.5,exp_time=100000,eps=0.0000000001):
    condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(condition)

    beta = params[0]
    alpha = 0.1
    cluster_var = params[1]
    hyper_mu = params[2]
    learn_rate = params[3]


    state = pf.initial_state(num_particles,alpha,cluster_var,hyper_mu=hyper_mu)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 5.5

    init_rho = 28
    rho = [init_rho] # estimate environment reward rate
    k = [1]# initialize to no decay, will keep a running average of this

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet,planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = all_decay[block][planet][prt-1]
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)
                    # mvt decay
                    k.append(all_decay[block][planet][prt-1])

                # crp
                expec_decay = expectation(state,pf.normalize(post+eps))
                v_stay_crp = expec_decay*reward
                v_leave_crp = (total_reward/total_time)*(harvest_time+iti)

                tau = time_constant(planet,prt,harvest_time,iti,travel_time)
                delta = reward/tau - rho[-1]
                # update estimate of environment rr
                new_rho =  rho[-1] + (1-((1-learn_rate)**tau))*delta
                #new_rho =  rho[-1] + alpha*delta
                rho.append(new_rho)
                estim_k = np.mean(k)

                # mvt
                v_stay_mvt = estim_k*reward
                v_leave_mvt = new_rho

                # combine
                v_stay = np.mean([v_stay_crp,v_stay_mvt])
                v_leave = np.mean([v_leave_crp,v_leave_mvt])

                prob_stay = 1 /(1 + np.exp(-beta*0.010*(v_stay - v_leave)))
                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*all_decay[block][planet][prt]

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp, true_planet



def crp_mvt_pos_neg(params,cond_num,num_particles,harvest_time=2,iti=1.5,travel_time=15.5,exp_time=100000,eps=0.0000000001):
    condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(condition)

    beta = params[0]
    alpha = 0.1
    cluster_var = params[1]
    hyper_mu = params[2]
    learn_rate_pos = params[3]
    learn_rate_neg = params[4]



    state = pf.initial_state(num_particles,alpha,cluster_var,hyper_mu=hyper_mu)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 5.5

    init_rho = 28
    rho = [init_rho] # estimate environment reward rate
    k = [1]# initialize to no decay, will keep a running average of this

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet, planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = all_decay[block][planet][prt-1]
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)
                    # mvt decay
                    k.append(all_decay[block][planet][prt-1])

                # crp
                expec_decay = expectation(state,pf.normalize(post+eps))
                v_stay_crp = expec_decay*reward
                v_leave_crp = (total_reward/total_time)*(harvest_time+iti)

                tau = time_constant(planet,prt,harvest_time,iti,travel_time)
                delta = reward/tau - rho[-1]
                # update estimate of environment rr
                if delta >= 0:
                    new_rho =  rho[-1] + (1-((1-learn_rate_pos)**tau))*delta
                else:
                    new_rho =  rho[-1] + (1-((1-learn_rate_neg)**tau))*delta
                #new_rho =  rho[-1] + alpha*delta
                rho.append(new_rho)
                estim_k = np.mean(k)

                # mvt
                v_stay_mvt = estim_k*reward
                v_leave_mvt = new_rho

                # combine
                v_stay = np.mean([v_stay_crp,v_stay_mvt])
                v_leave = np.mean([v_leave_crp,v_leave_mvt])

                prob_stay = 1 /(1 + np.exp(-beta*0.010*(v_stay - v_leave)))
                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*all_decay[block][planet][prt]

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp, true_planet


def crp_mvt_two_softmax(params,cond_num,num_particles,harvest_time=2,iti=1.5,travel_time=15.5,exp_time=100000,eps=0.0000000001):
    condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(condition)

    beta_crp = params[0]
    beta_mvt = params[1]
    alpha = 0.1
    cluster_var = params[2]
    hyper_mu = params[3]
    learn_rate = params[4]


    state = pf.initial_state(num_particles,alpha,cluster_var,hyper_mu=hyper_mu)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 5.5

    init_rho = 28
    rho = [init_rho] # estimate environment reward rate
    k = [1]# initialize to no decay, will keep a running average of this

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet,planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = all_decay[block][planet][prt-1]
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)
                    # mvt decay
                    k.append(all_decay[block][planet][prt-1])

                # crp
                expec_decay = expectation(state,pf.normalize(post+eps))
                v_stay_crp = expec_decay*reward
                v_leave_crp = (total_reward/total_time)*(harvest_time+iti)

                tau = time_constant(planet,prt,harvest_time,iti,travel_time)
                delta = reward/tau - rho[-1]
                # update estimate of environment rr
                new_rho =  rho[-1] + (1-((1-learn_rate)**tau))*delta
                #new_rho =  rho[-1] + alpha*delta
                rho.append(new_rho)
                estim_k = np.mean(k)

                # mvt
                v_stay_mvt = estim_k*reward
                v_leave_mvt = new_rho

                prob_stay = 1 /(1 + np.exp(0.010*(-beta_mvt*v_stay_mvt -beta_crp*v_stay_crp + beta_mvt*v_leave_mvt + beta_crp*v_leave_crp)))

                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                reward = reward*all_decay[block][planet][prt]

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp, true_planet



def crp_td(params,cond_num,num_particles,harvest_time=2,iti=1.5,travel_time=15.5,exp_time=100000,eps=0.0000000001):
    condition = condition_type(cond_num)
    ___, rho_0, all_decay = load_data(condition)

    beta_crp = params[0]
    beta_td = params[1]
    alpha = 0.1
    cluster_var = params[2]
    hyper_mu = params[3]
    learn_rate = params[4]
    gamma = 0.7

    # for td
    rho_init = 28/(1-gamma)

    q_val_bins = get_bins(135,0.9)
    q_val_bins.insert(0,0)
    num_states = len(q_val_bins) + 1
    q_vals_stay = np.ones(num_states)*rho_init # states are represented by the reward you just received, the value of staying is state dependent while the value of exiting is not
    q_exit = rho_init # q-value for exiting is the same regardless of state

    # for crp
    state = pf.initial_state(num_particles,alpha,cluster_var,hyper_mu=hyper_mu)

    # save important variables here
    choices = []
    all_reward_exp = [] # reward list of the simulation
    n_blocks = 5
    block_max = 300
    n_planets = 20

    total_reward = 0
    total_time = 5.5

    planet = 0
    true_planet = []
    max_k = state["max_k"]
    post = np.concatenate((np.ones((num_particles,1)),np.zeros((num_particles,max_k-1))),axis=1)

    for block in range(n_blocks):
        block_time, planet, prt, block_choice = initialize_block()
        while (block_time < block_max) & (planet < n_planets):
            reward_exp, on_planet, reward, true_planet,planet_decay = initialize_planet(rho_0,block,planet,true_planet)
            while (block_time < block_max) & on_planet:
                total_reward += reward
                reward_exp.append(reward)
                block_time += (harvest_time+iti)
                total_time += (harvest_time+iti)
                # calc decay experienced
                if prt > 0:
                    actual_decay = all_decay[block][planet][prt-1]
                    planet_decay.append(actual_decay) # save for inference over which patch type we're in

                    # do inference on which cluster in
                    curr_prior = pf.prior(state) # retrieve prior expectation of being in a state
                    log_prior = np.log(curr_prior+eps)
                    curr_log_likelihood = pf.log_likelihood(state,planet_decay)
                    post = pf.posterior(log_prior,curr_log_likelihood)

                # crp
                expec_decay = expectation(state,pf.normalize(post+eps))
                v_stay_crp = expec_decay*reward
                v_leave_crp = (total_reward/total_time)*(harvest_time+iti)

                # td
                curr_state = int(np.searchsorted(q_val_bins,reward,side='right'))-1
                prob_stay = 1 /(1 + np.exp(-beta_td*0.010*(q_vals_stay[curr_state] - q_exit)))
                v_curr_state = prob_stay*q_vals_stay[curr_state] + (1-prob_stay)*q_exit
            #    update values
                if (planet != 0) & (prt == 0): # first reward on planet but not the first planet because didn't choose to stay or leave
            # updating the value of the state we just left
                    tau = travel_time+harvest_time+iti

                    delta = (gamma**tau)*reward + (gamma**tau)*v_curr_state - q_exit
                    q_exit= q_exit + alpha*delta
                elif prt > 0: # if not first dig on planet
                    tau = harvest_time + iti
                    last_state = int(np.searchsorted(q_val_bins,last_reward,side='right'))-1

                    delta = reward + (gamma**tau)*v_curr_state - q_vals_stay[last_state]
                    q_vals_stay[last_state] = q_vals_stay[last_state] + alpha*delta

                # td
                v_stay_td = q_vals_stay[curr_state]
                v_leave_td= q_exit
                prob_stay = 1 /(1 + np.exp(0.010*(-beta_td*v_stay_td -beta_crp*v_stay_crp + beta_td*v_leave_td + beta_crp*v_leave_crp)))


                curr_prt = prt
                choice, on_planet, prt = make_choice(prob_stay,prt)
                block_choice.append(choice)
                last_reward = reward
                reward = reward*all_decay[block][planet][prt]

            # update params for monitoring environment reward rate
            if (curr_prt > 0) & (on_planet==False):
                pf.resample_and_update_particles(state,post,planet_decay)
            all_reward_exp.append(reward_exp)
            planet += 1
            block_time += travel_time
            total_time += travel_time
        choices.append(block_choice)
    return choices, all_reward_exp, true_planet
###############################################################################

def get_prts(data):
    split_list = list(split_after(data, lambda x: x == 1))
    prts = [len(lst) for lst in split_list]
    return prts

def run_sim_all_sub(data,param_dict):
    all_sim_prt = {} # make a dictionary to keep all prts from simulations
    all_sim_rewards = {}
    subs = list(set(data["sub_num"]))
    for sub in subs:
        sub_dict = param_dict.loc[param_dict["sub"]==0]
        params =[sub_dict["alpha"][0],sub_dict["cluster_var"][0]]
        reward_list, galaxy_list = param.get_sub_data(all_data,sub)
        sim_prt,sim_reward_list = crp(params,reward_list,galaxy_list)
        prts = get_prts(sim_prt)
        all_sim_prt[sub] = prts
        all_sim_rewards[sub] = sim_reward_list
    return all_sim_prt,all_sim_rewards

def main():
    cond_num = int(sys.argv[1])
    num_particles = int(sys.argv[2])

    params = [12,0.005,0.002]

    choices, all_reward_exp = crp_mvt(params,cond_num,num_particles,harvest_time=2,iti=1.5,travel_time=15.5,exp_time=100000)

    prts =  [get_prts(block) for block in choices]

    print(prts)

if __name__ == "__main__":
    main()
