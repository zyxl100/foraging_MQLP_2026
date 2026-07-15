using CSV
using DataFrames
using Random, Distributions

include("particle_filter.jl")
Random.seed!(1234) # set random seed 

###############################################################################################
# set up task timing in seconds 
struct Timing
    harvest::Float64
    travel::Float64
    iti::Float64
    alien::Float64
end

# set up task structure 
struct Exp
    n_blocks::Float64
    max_time_in_block::Float64 # in seconds 
    max_planets_in_block::Float64
end 

###############################################################################################
# functions to generate observations 

function get_init_reward()
    sample = rand(Normal(100,5))
    return round(max(min(135,sample),0))
end

function get_decay(galaxy)
    if galaxy == 0
        return rand(Beta(13,51))
    elseif galaxy == 1
        return rand(Beta(50,50))
    else
        return rand(Beta(50,12))
    end
end

###############################################################################################
# functions to grab different subsections of data 

function get_block(data, block_num)
    return data[in(block_num).(data.block),:]
end 

function get_planet(data,planet_num)
    return data[in(planet_num).(data.planet),:]
end

function get_galaxy(data, block_planet_num)
    return data[in(block_planet_num).(data.planet),:].galaxy[1]
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
# helper function 
function tally(zd,K)
    ret = zeros(Int64, K)
    for k in zd
        ret[k] += 1
    end
    return ret
end

###############################################################################################

function initialize_block(data, block_num)
    block = get_block(data, block_num)
    time_in_block = 0
    planet_num_in_block = 0
    return block, time_in_block, planet_num_in_block
end 

function initialize_planet(data,planet_num)
    galaxy = get_galaxy(data, planet_num)
    init_reward = get_init_reward()
    decays = []
    stay_num = 0
    return galaxy, init_reward, decays, stay_num
end 
###############################################################################################

function observe_reward(galaxy, last_reward)
    return round(get_decay(galaxy)*last_reward)
end

function compute_v_stay(last_reward,all_decays)
    return last_reward*mean(all_decays)
end

function select_action(v_stay, v_leave, beta, epsilon)
    if rand() < epsilon
        return rand() < 0.5 ? 0 : 1
    else 
        p_stay = (1-epsilon)/(1+exp(-beta*(v_stay-v_leave))) + (epsilon/2)
        return rand() < p_stay ? 1 : 0
    end 
end 

function update_decays(planet_decays, new_reward, old_reward)
    if old_reward > 0
        append!(planet_decays,new_reward/old_reward)
    end
    return planet_decays     
end

function update_time(old_block_time, old_total_time, tau)
    return old_block_time + tau, old_total_time + tau
end 

function update_data(data, block_num, planet_num, galaxy, reward, stay_num)
    new_row = DataFrame("block_num"=>block_num, "planet_num"=>planet_num, "galaxy"=> galaxy, "reward"=> reward, "stay_num"=>stay_num)
    return vcat(data,new_row)
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

function sample_v_stay(particle_filter, weights, prob_k, n_samples, data)
    values = zeros(n_samples)
    all_clus = zeros(n_samples)

    @inbounds for s in 1:n_samples
        # 1. sample a particle
        cum_weight = cumsum(weights)
        sampled_particle = argmax(rand() .< cum_weight) # try another way to make sure it works

        # 2. sample a cluster
        cum_particle_post = cumsum(prob_k[sampled_particle])
        cluster = argmax(rand() .< cum_particle_post) # try another way to make sure it works
        all_clus[s] = cluster

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

function linearize(g_base,g_coef,u)
    return 1/(1+exp(-(g_base + g_coef*u)))
end

function compute_planning_horizon(cluster_counts::Vector{Float64}, n_samples::Int64, gamma_base::Float64, gamma_coef::Float64)
    cluster_counts = round.(Int, cluster_counts) # count the number of times cluster was sampled during monte carlo sampling procedure 
    K = maximum(cluster_counts) # maximum number of clusters
    dist = Multinomial(n_samples,tally(cluster_counts,K)/n_samples) # define multinomial distribution 
    model_uncertainty = entropy(dist) # take entropy 
    return linearize(gamma_base, gamma_coef,model_uncertainty) # use entropy to set the discounting rate 
end



function evaluation_uncertainty_adapt(reward::Float64, planet_decays::Vector{Any}, global_rr::Float64, stay_time::Float64, N::Int64, bundle_of_particles::Vector{Particle}, w::Vector{Float64}, sim_samples::Int64, alpha::Float64, g_base::Float64, g_coef::Float64)
    prob_k = prob_cluster(planet_decays, N, alpha, bundle_of_particles)  # get probability of each cluster
    samples, clusters = sample_v_stay(bundle_of_particles, w, prob_k, sim_samples, planet_decays) # sample from decay rate distributions 
    
    gamma_effective = compute_planning_horizon(clusters, sim_samples, g_base, g_coef)

    v_stay = mean(samples)*reward # predict the reward that will be recieved on the next trial 
    v_leave = global_rr*stay_time*(gamma_effective) # opportunity cost of current patch discounted by the future discounting term 
    
    return v_stay, v_leave

end

###############################################################################################

function crp(params,num_particles=200)
    # initialize the particle filter
    alpha = params[1]
    gamma_base = params[2]
    gamma_coef = params[3]

    # action selection params 
    beta = params[4] 
    eps = params[5] 

    # intialize the exp
    planet_order = DataFrame(CSV.File("../../exp_struc.csv"))
    exp = Exp(4,360,20) # number of blocks, max time in block, max number of planets visited in block 
    timing = Timing(3,10,1.5,5.5) # harvest time, travel time, iti, alien time 

    hyper_mu = 0.5
    hyper_var = 0.25
    hyper_tau = 1.0
    n_samples = 1000
    particles, weights = init_particle_filter(num_particles,hyper_mu, hyper_var, hyper_tau, alpha)

    # initialize for tracking progress through the exp
    total_reward = 0
    total_time = timing.alien
    total_planet_n = 0 

    # dataframe to save data 
    simulated_data = DataFrame()

    for b in 1:exp.n_blocks
        # get current block 
        curr_block, time_in_block, planet_num_in_block = initialize_block(planet_order,b)
        time_in_block += timing.alien
        while (time_in_block < exp.max_time_in_block) & (planet_num_in_block < exp.max_planets_in_block)
            # initialize 
            galaxy, init_reward, planet_decays, stay_num = initialize_planet(planet_order, planet_num_in_block)
            total_reward += init_reward 

            # update rho 
            tau = get_time_constant("stay", timing)
            time_in_block, total_time = update_time(time_in_block, total_time, tau)
            v_stay, v_leave = evaluation_uncertainty_adapt(init_reward, planet_decays, total_reward/total_time, get_time_constant("stay", timing), total_planet_n, particles, weights, n_samples, alpha, gamma_base, gamma_coef)
        
            # stay again? 1 = yes, 0 = no 
            action = select_action(v_stay, v_leave, beta, eps)

            # update data
            simulated_data = update_data(simulated_data, b, total_planet_n, galaxy, init_reward, stay_num)
            last_reward = init_reward 
            while action == 1
                stay_num += 1 
                
                # observe reward update total reward
                reward = observe_reward(galaxy, last_reward)
                total_reward += reward 
                planet_decays = update_decays(planet_decays, reward, last_reward)
            
                # update total time 
                tau = get_time_constant("stay", timing)
                time_in_block, total_time = update_time(time_in_block, total_time, tau)

                # stay again? need to compute action values 
                v_stay, v_leave = evaluation_uncertainty_adapt(reward, planet_decays, total_reward/total_time, get_time_constant("stay", timing), total_planet_n, particles, weights, n_samples, alpha, gamma_base, gamma_coef)
                action = select_action(v_stay, v_leave, beta, eps)

                # update data 
                simulated_data = update_data(simulated_data, b, total_planet_n, galaxy, reward, stay_num)
                last_reward = reward
            end
            # update clusters with new observations  
            if length(planet_decays) > 0
                prob_k = prob_cluster(planet_decays, total_planet_n, alpha, particles)  # get probability of each cluster
                particles, weights = resample_and_update_particles(particles, weights, prob_k, planet_decays)
            end

            # update time 
            tau = get_time_constant("leave", timing)
            time_in_block, total_time = update_time(time_in_block, total_time, tau)

            planet_num_in_block += 1
            total_planet_n += 1
        end
    end
    # save generating data 
    simulated_data.alpha = repeat([alpha], nrow(simulated_data))
    simulated_data.gamma_base = repeat([gamma_base], nrow(simulated_data))
    simulated_data.gamma_coef = repeat([gamma_coef], nrow(simulated_data))
    simulated_data.beta = repeat([beta], nrow(simulated_data))
    simulated_data.epsilon = repeat([eps], nrow(simulated_data))

    return simulated_data
end

###############################################################################################

function sample_parameters(alpha)
    if alpha == 0
        gamma_coef = 0.0 # set to 0 because state space uncertainty will always be 0 when alpha is 0
    else
        gamma_coef = rand(Uniform(-3.0,  3.0))
    end 

    gamma_base = rand(Uniform(-10.0, 10.0))
    beta = rand(Uniform(0.0, 1.0))
    eps = rand(Uniform(0.0, 0.10))
    return [alpha, gamma_base, gamma_coef, beta, eps]
end 


function main()
    alpha = parse(Float64,ARGS[1])
    n_subs = 500
    all_data = DataFrame()
    for sub = 1:n_subs
        sub_params = sample_parameters(alpha)
        sub_data = crp(sub_params)
        sub_data.sub_id = repeat([sub], nrow(sub_data))

        all_data = vcat(all_data,sub_data)
    end
    CSV.write("gen_data/alpha_"*string(alpha)*".csv",all_data)
end

main()

