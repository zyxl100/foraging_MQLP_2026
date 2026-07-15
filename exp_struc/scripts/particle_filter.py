import pandas as pd
import numpy as np
from collections import namedtuple, Counter
import scipy
from scipy import stats
from numpy import random
import copy

def initial_state(num_particles,alpha,prior_tau,max_k=15,hyper_mu=0.5,hyper_var=0.1):
    cluster_count =  np.zeros((num_particles,max_k))

    state = {
        "hyper_parameters_": { # parameters to describe the global distribution, base distribution
            "mean": hyper_mu,
            "variance": hyper_var,
        },
        "cluster_parameters": {
            "mean" : np.ones((num_particles,max_k))*hyper_mu,
            "variance": np.ones((num_particles,max_k))*hyper_var,
        },
        "cluster_counts": cluster_count, # mixing proportions,
        "cluster_points": {p: {k: [] for k in range(max_k)} for p in range(num_particles)}, # the means
        "tau":prior_tau,
        "alpha_": alpha,
        "max_k": max_k,
        "num_particles": num_particles,
        "weights": np.array([1/num_particles]*num_particles), # all give equal weighting
        "memories": {new_list: {} for new_list in range(num_particles)}
    }
    return state

def prior(state):
    """ Grab the array with the occurences of each cluster """
    N = np.sum(state['cluster_counts'][0,:])# number of experiences
    alpha = state["alpha_"]
    hyper_mu = state["hyper_parameters_"]["mean"]

    prior = copy.deepcopy(state["cluster_counts"])
    new_cluster_id = np.argmax(prior == 0,axis=1)
    prior[np.arange(len(prior)), new_cluster_id] = alpha
    prior = prior/(N + alpha)

    return prior


def hyper_prior_update(state,p,cluster,count,data):
    prior_mu = state["cluster_parameters"]["mean"][p,cluster]
    prior_var = state["cluster_parameters"]["variance"][p,cluster]
    prior_tau = state["tau"]
    prior_n = count
    n = len(data)
    mu_bar = np.mean(data)

    # https://en.wikipedia.org/wiki/Normal_distribution#With_unknown_mean_and_unknown_variance

    posterior_mu = (prior_n*prior_mu + mu_bar)/(prior_n + n)
    posterior_n = prior_n + n
    posterior_tau = prior_tau + n
    posterior_tau_var = prior_tau*prior_var + ((prior_n)/(posterior_n))*((prior_mu - mu_bar)**2)
    posterior_var = posterior_tau_var/posterior_tau

    state["cluster_parameters"]["mean"][p,cluster] = posterior_mu
    state["cluster_parameters"]["variance"][p,cluster] = posterior_var
    state["tau"] = posterior_tau

    return

def mean_square_error(data):
    mu = np.mean(data)
    square_error = []

    for d in data:
        square_error.append((d-mu)**2)
    return sum(square_error)

def cluster_param_update(state,p,cluster,count,data):
    prior_mu = state["cluster_parameters"]["mean"][p,cluster]
    prior_var = state["cluster_parameters"]["variance"][p,cluster]
    prior_tau = state["tau"]
    prior_n = count
    n = len(data)
    mu_bar = np.mean(data)

    # https://en.wikipedia.org/wiki/Normal_distribution#With_unknown_mean_and_unknown_variance

    posterior_mu = (prior_n*prior_mu + n*mu_bar)/(prior_n + n)
    posterior_n = prior_n + n
    posterior_tau = prior_tau + n
    posterior_tau_var = prior_tau*prior_var +  mean_square_error(data) +((prior_n*n)/(prior_n +n))*((prior_mu - mu_bar)**2)
    posterior_var = posterior_tau_var/posterior_tau

    state["cluster_parameters"]["mean"][p,cluster] = posterior_mu
    state["cluster_parameters"]["variance"][p,cluster] = posterior_var
    state["tau"] = posterior_tau

    return


def log_likelihood(state,new_data):
    """ Get the likelihood of observing this data from all the different clusters """
    cluster_mu = state["cluster_parameters"]["mean"]
    cluster_var = state["cluster_parameters"]["variance"]
    cluster_sd = np.sqrt(cluster_var)

    max_k = state["max_k"]
    num_particles = state["num_particles"]
    new_data = np.array(new_data).reshape(-1,1,1)
    all_ll = stats.norm.logpdf(new_data,loc=cluster_mu,scale=cluster_sd).sum(0)
    return all_ll

def log_likelihood_partition(state,particle_num):
    cluster_points = state["cluster_points"][particle_num]
    cluster_mu = state["cluster_parameters"]["mean"][particle_num,:]
    cluster_var = state["cluster_parameters"]["variance"][particle_num,:]
    cluster_sd = np.sqrt(cluster_var)
    max_k = state["max_k"]

    #log_lik = 0
    log_lik = []
    for k in range(max_k): # loop thru clusters
        if len(cluster_points[k]) > 0:
            ll = stats.norm.logpdf(cluster_points[k],loc=cluster_mu[k],scale=cluster_sd[k])[0]
            log_lik += [ll]
    if len(log_lik) > 0:
        return scipy.special.logsumexp(log_lik)
    else:
        return 0


def normalize(post_full):
    """Normalize distribution  """
    return post_full/(post_full.sum(axis=1))[:,None]

def posterior(log_prior,log_likelihood):
    #post_full = scipy.special.logsumexp(np.log(prior+0.0000001))+log_likelihood
    post_full = log_prior+log_likelihood
    post_full = np.exp(post_full)
    return post_full

def resample_and_update_particles(state,post,data,eps=0.0000000001):
    num_particles = state["num_particles"]

    if num_particles == 1:
        post = post/sum(post)
        # cluster assignment
        cluster = np.argmax(random.uniform(0, 1) < np.cumsum(post/sum(post)));
        state["cluster_counts"][cluster] += 1
        state["cluster_points"][cluster] += data

        count = state["cluster_counts"][cluster]
        theta = np.mean(state["cluster_points"][cluster])

        posterior_mu, posterior_sigma2 = cluster_param_update(state,count,theta)

        state["cluster_parameters"]["mean"][cluster] = posterior_mu
        state["cluster_parameters"]["variance"][cluster] = posterior_sigma2

    else:
        old_weights = copy.deepcopy(state["weights"])
        old_counts = copy.deepcopy(state["cluster_counts"])
        old_cluster_points = copy.deepcopy(state["cluster_points"])
        eta = 0

        cum_weight =np.cumsum(old_weights)
        cum_cluster_by_row = np.cumsum(normalize(post+eps),axis=1)

        for p in range(num_particles):
            # sample paricle based on previous weights
            row = np.argmax(random.uniform(0, 1) < cum_weight)
            state["cluster_counts"][p,:] = old_counts[row,:]
            state["cluster_points"][p] = old_cluster_points[row]
            #state["memories"][p,:] = old_memories[row]

            # do cluster assignment based on the sampled cluster and update parameters
            cluster = np.argmax(random.uniform(0, 1) < cum_cluster_by_row[row,:])
            count = len(state["cluster_points"][p][cluster])
            cluster_param_update(state,p,cluster,count,data)
            state["cluster_counts"][p,cluster] += 1
            state["cluster_points"][p][cluster] += data


            # calculate the log likelihood of this partion to update the weights for the next time we resample
            new_weight = log_likelihood_partition(state,p)
            if (np.isnan(new_weight)) | (new_weight==0):
                new_weight = eps
            state["weights"][p] = new_weight
            eta += new_weight

        state["weights"] = state["weights"]/eta
    return
