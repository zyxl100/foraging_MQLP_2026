using CSV
using DataFrames
using Random, Distributions
using Serialization 

include("particle_filter.jl")

Random.seed!(1234) # set random seed 

###############################################################################################

struct Timing
    harvest::Float64
    travel::Float64
    iti::Float64
    alien::Float64
end

struct Exp
    n_blocks::Float64
    max_time_in_block::Float64
    max_planets_in_block::Float64
end 

###############################################################################################

function get_planet(data,planet_num)
    return data[in(planet_num).(data.planet_num),:]
end

function get_trial(planet_data,trial_on_planet_num)
    return planet_data[in(trial_on_planet_num).(planet_data.stay_num),:]
end

function get_time_constant(action, timing_struct)
    if action == "leave"
        return timing_struct.travel + timing_struct.alien 
    else
        return timing_struct.harvest + timing_struct.iti
    end
end
###############################################################################################

function initialize_planet(data, planet_num)
    curr_planet = get_planet(data,planet_num)
    n_stay_decisions = findmax(curr_planet.stay_num)[1]
    planet_decays = []

    curr_trial = get_trial(curr_planet,0)
    init_reward = curr_trial.reward[1]
    return curr_planet, n_stay_decisions, planet_decays, init_reward
end 

###############################################################################################
# helper function 
function tally(zd,K)
    ret = zeros(Int64, K)
    for k in zd
        ret[k] += 1
    end
    return ret
end

function update_decays(planet_decays, new_reward, old_reward)
    if old_reward > 0
        append!(planet_decays,new_reward/old_reward)
    end
    return planet_decays     
end

###############################################################################################
# CHINESE RESTAURANT PROCESS FUNCTIONS 

function calc_posterior(decay_list, N, alpha, particle_filter)
    num_particles = length(particle_filter)
    posterior = [[] for i = 1:num_particles]
    for p in 1:num_particles
        # 1. get log prior
        log_prior = log_prior_particle(particle_filter[p],N,alpha)
        # 2. get log likelihood
        log_like = log_likelihood_particle(particle_filter[p],decay_list)
        # 3. combine to get posterior
        post = exp.(log_prior .+ log_like)

        post_norm = post/sum(post)
        posterior[p] = post_norm
    end
    return posterior
end


function prob_cluster(decay_list, N, alpha, particle_filter)
    if (N == 0) | (length(decay_list) == 0) # no observations in task at all or no observations on the current planet 
        return prior(particle_filter, N , alpha)
    else
        return calc_posterior(decay_list, N, alpha, particle_filter)
    end
end

function sample_v_stay(particle_filter::Vector{Particle}, weights::Vector{Float64}, prob_k::Vector{Vector{Any}}, n_samples::Int64, data::Vector{Any})
    values = zeros(n_samples)
    all_clus = zeros(n_samples)
    all_clus_n = zeros(n_samples)

    @inbounds for s in 1:n_samples
        # 1. sample a particle
        cum_weight = cumsum(weights)
        sampled_particle = argmax(rand() .< cum_weight) # try another way to make sure it works

        # 2. sample a cluster
        cum_particle_post = cumsum(prob_k[sampled_particle])
        cluster = argmax(rand() .< cum_particle_post) # try another way to make sure it works
        all_clus[s] = cluster
        all_clus_n[s] = length(particle_filter[sampled_particle].cluster_mean)
        # 3. sample from the distribution associated with this particle's cluster that was sampled
        if cluster > length(particle_filter[sampled_particle].cluster_mean)
            # create a new distribution for the new latent cause 
            mu = particle_filter[sampled_particle].hyper_mu
            sigma = particle_filter[sampled_particle].hyper_var^(1/2)
        else
            # might want to conform expectation to the data
            mu = particle_filter[sampled_particle].cluster_mean[cluster]
            sigma = particle_filter[sampled_particle].cluster_variance[cluster]^(1/2)
        end

        d = Normal(mu,sigma)
        sampled_value = rand(d)
        values[s] = sampled_value
    end
    return values, all_clus
end


function get_reward_uncertainty(alpha, particles, particle_weights, n_samples, n_planet, last_reward, curr_planet_decays)
    prob_k = prob_cluster(curr_planet_decays, n_planet, alpha, particles)  # get probability of each cluster
    samples, cluster_counts = sample_v_stay(particles, particle_weights, prob_k, n_samples, curr_planet_decays) # sample from decay rate distributions 

    cluster_counts = round.(Int, cluster_counts) # count the number of times cluster was sampled during monte carlo sampling procedure 
    K = maximum(cluster_counts) # maximum number of clusters
    dist = Multinomial(n_samples,tally(cluster_counts,K)/n_samples) # define multinomial distribution 
    model_uncertainty = entropy(dist) # take entropy 

    next_reward = mean(samples)*last_reward # predict the reward that will be recieved on the next trial 
    return next_reward, model_uncertainty
end


###############################################################################################

function crp_only(data, exp, timing, alpha, num_particles=200)
    hyper_mu = 0.5
    hyper_var = 0.25
    hyper_tau = 1.0
    n_samples = 1000
    particles, weights = init_particle_filter(num_particles,hyper_mu, hyper_var, hyper_tau, alpha)

    # initialize for tracking progress through the exp
    choice_num = 0
    total_planet_n = 0
    max_planets = findmax(data.planet_num)[1]
    total_reward = 0
    total_time = timing.alien
    
    # store to return at the end  
    all_predictions = NamedTuple{(:choice_num, :pred_reward, :reward_uncert, :global_rr, :planet_stay_num, :max_planet_stay_num)}[]
    for p in 0:max_planets 
        curr_planet, n_stay_decisions, planet_decays, init_reward  = initialize_planet(data, p)
        total_reward += init_reward 
        tau = get_time_constant("stay", timing)
        total_time += tau 
        
        # compute prediction of next reward and uncertainty over prediction 
        pred_reward, reward_uncert = get_reward_uncertainty(alpha, particles, weights, n_samples, total_planet_n, init_reward, planet_decays)
        choice_num += 1
        last_reward = init_reward 

        # update        
        global_rr = total_reward/total_time
        planet_stay_num = 0 
        max_planet_stay_num = n_stay_decisions
        push!(all_predictions,(;choice_num,pred_reward,reward_uncert,global_rr,planet_stay_num,max_planet_stay_num))
        
        for s in 1:n_stay_decisions 
            # get trial 
            curr_trial = get_trial(curr_planet,s)

            # observe reward 
            reward = curr_trial.reward[1]
            total_reward += reward 
            planet_decays = update_decays(planet_decays, reward, last_reward)
            
            # update total time 
            tau = get_time_constant("stay", timing)
            total_time += tau 

            # compute prediction of next reward and uncertainty over prediction 
            pred_reward, reward_uncert = get_reward_uncertainty(alpha, particles, weights, n_samples, total_planet_n, reward, planet_decays)
            choice_num += 1
            last_reward = reward 
            
            # update 
            global_rr = total_reward/total_time
            planet_stay_num = s
            push!(all_predictions,(;choice_num,pred_reward,reward_uncert,global_rr,planet_stay_num,max_planet_stay_num))

        end
        if length(planet_decays) > 0
            prob_k = prob_cluster(planet_decays, total_planet_n, alpha, particles)  # get probability of each cluster
            particles, weights = resample_and_update_particles(particles, weights, prob_k, planet_decays)
        end
            
        tau = get_time_constant("leave", timing)
        total_time += tau 
        total_planet_n += 1

    end 
    # construct a dataframe to return 
    return all_predictions
end 

###############################################################################################
function get_model_name(model_num)   
    if model_num == 0 # mvt 
        return "alpha_0"
    elseif model_num == 1
        return "alpha_02"
    end 
end


function monte_carlo_sample_latents(generative_model_num, alpha_level, sub_num, data, n_runs=1000)
    exp_struc = Exp(4,360,20) # number of blocks, max time in block, max number of planets visited in block 
    exp_timing = Timing(3,10,1.5,5.5) # harvest time, travel time, iti, alien time 

    if alpha_level == 0 
        alpha = 0.0
    elseif alpha_level == 1
        alpha = 0.2    
    end 

    # sample planet type assignments 
    crp_predictions = map(1:n_runs) do i
        println(i)
        crp_only(data, exp_struc, exp_timing, alpha)
    end

    # save crp_predictions to folder 
    file_name = string("fit_data/gen_", get_model_name(generative_model_num), "_fit_", get_model_name(alpha_level), "/crp_latents/sub", string(sub_num), ".ser")
    serialize(file_name, crp_predictions)
end

function get_sub_data(generative_model_num, subject_num)
    data = DataFrame(CSV.File(string("gen_data/", get_model_name(generative_model_num), ".csv")))
    return data[in(subject_num).(data.sub_id),:]
end 

function main()
    gen_model_num = parse(Int64,ARGS[1])
    sub_num = parse(Int64,ARGS[2])
    alpha_level = parse(Int64,ARGS[3])

    sub_data = get_sub_data(gen_model_num, sub_num)

    monte_carlo_sample_latents(gen_model_num, alpha_level, sub_num, sub_data)
end

main()