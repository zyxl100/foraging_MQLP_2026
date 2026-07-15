# ##############################
# # simulate_structLearning_softmax.jl
# # Self-contained simulation script
# ##############################

# using CSV
# using DataFrames
# using Random, Distributions
# using Statistics
# using StatsBase

# # load infrastructure
# include("./particle_filter.jl")
# include("./model_struct.jl")
# include("./opt.jl")

# # load all helper functions like get_planet, get_galaxy, get_reward, etc.
# include("./model.jl")     # <-- ADD THIS



# ############################################################
# # 1. PARAMETER STRUCT AND SAMPLING FUNCTION
# ############################################################

# struct SLParams
#     alpha::Float64       # CRP cluster rate
#     gamma_base::Float64
#     gamma_coef::Float64
# end

# function sample_subject_params(n_sub::Int; rng=Random.default_rng())
#     dist_gamma_base = Uniform(-10.0, 10.0)
#     dist_gamma_coef = Uniform(-3.0, 3.0)
#     dist_alpha      = Uniform(0.0, 10.0)

#     out = Vector{SLParams}(undef, n_sub)
#     for i in 1:n_sub
#         out[i] = SLParams(
#             rand(rng, dist_alpha),
#             rand(rng, dist_gamma_base),
#             rand(rng, dist_gamma_coef)
#         )
#     end
#     return out
# end


# ############################################################
# # 2. STRUCTURAL LEARNING MODEL 
# ############################################################

# function crp_adaptiveDiscount_softmax(data,params,num_particles)
#     # intialize the exp
#     expt = Experiment(5,360,20,2,10,5.5,1.5)
#     behav = Behavior([],[],[],[])

#     # initialize the particle filter
#     alpha = params[1]
#     gamma_base = params[2]
#     gamma_coef = params[3]
#     #println(params)
#     hyper_mu = 0.5
#     hyper_var = 0.25
#     hyper_tau = 1
#     n_samples = 100
#     particles, weights = init_particle_filter(num_particles,hyper_mu, hyper_var, hyper_tau, alpha)

#     # initialize for tracking progress through the exp
#     total_reward = 0
#     total_time = expt.alien_time + expt.iti
#     N = 0 # all planets experienced, ***check if changes if I change to number of decay rates ***
#     n_cluster_inferred = []
#     gammas = []
#     pred_decay = []
#     uncertainty=[]
#     true_decay=[]
#     middle = []
#     middle_decay = []
#     for b in 1:expt.n_blocks
#         curr_block = data[in(b).(data.block),:]
#         b_tracker = Block_Tracker(expt.alien_time,0)
#         while (b_tracker.block_time < expt.block_max_time) & (b_tracker.planet < expt.block_n_planet)
#             curr_planet, p_tracker = get_planet(b, b_tracker,curr_block)
#             while (b_tracker.block_time < expt.block_max_time) & p_tracker.on_planet

#                 # dig up reward and add to list
#                 p_tracker, total_reward = get_reward(p_tracker, total_reward, curr_planet)

#                 # add time that it took to dig it up
#                 b_tracker.block_time += expt.harvest_time + expt.iti
#                 total_time += expt.harvest_time + expt.iti

#                 # probability of cluster
#                 global prob_k = prob_cluster(p_tracker.curr_reward, p_tracker.decay_list, N, alpha, particles)
#                 samples,clusters = sample_v_stay(particles,weights, prob_k, n_samples,p_tracker.decay_list)
#                 global samples_all = samples

#                 clusters = round.(Int, clusters)
#                 K = maximum(clusters)
#                 append!(n_cluster_inferred,length(prob_k[1]))
#                 d =Multinomial(n_samples,tally(clusters,K)/n_samples)
#                 model_uncertainty = entropy(d)
#                 gamma_effective = 1/(1+exp(-(gamma_base - gamma_coef*model_uncertainty)))
#                 v_stay = mean(samples)*p_tracker.curr_reward
#                 v_leave = (total_reward/total_time)*(expt.harvest_time + expt.iti)*gamma_effective
#                 p_tracker =  make_choice_max(v_stay, v_leave, p_tracker)
#                 append!(middle,[tally(clusters,K)])
#                 append!(middle_decay,[deepcopy(p_tracker.decay_list)])

#             end
#             append!(uncertainty,var(samples_all))
#             append!(pred_decay,mean(samples_all))
#             append!(middle,[[]])
#             append!(middle_decay,[[]])


#             if p_tracker.prt > 1
#                 particles, weights = resample_and_update_particles(particles,weights,prob_k,p_tracker.decay_list)
#             end

#             if p_tracker.prt > 1
#                 append!(true_decay,mean(p_tracker.decay_list))
#             else
#                 append!(true_decay,0)
#             end
#             b_tracker.block_time += expt.travel_time + expt.alien_time
#             b_tracker.planet += 1
#             total_time += expt.travel_time + expt.alien_time
#             behav = update_behavior(behav, p_tracker)
#             N += 1
#         end
#     end
#     return behav
# end


# ############################################################
# # 3. SIMULATION WRAPPER
# ############################################################

# function simulate_structLearner_softmax(
#     n_sub::Int;
#     num_particles::Int = 50,
#     template_data_path::String = "data/all_data_new.csv",
#     save_path::String = "simulated_structLearner_softmax_1000subs.csv"
# )
#     # Load template structure (use the first subject)
#     all_data = DataFrame(CSV.File(template_data_path, delim = ','))
#     first_sub = all_data.sub_num[1]
#     template  = all_data[in(first_sub).(all_data.sub_num), :]

#     # Sample parameters
#     param_draws = sample_subject_params(n_sub)

#     sim_all = DataFrame()

#     for s in 1:n_sub
#         p = param_draws[s]

#         params_vec = [
#             p.alpha,
#             p.gamma_base,
#             p.gamma_coef
#         ]

#         behav = crp_adaptiveDiscount_softmax(template, params_vec, num_particles)

#         n_planets = length(behav.true_planet)
#         mean_reward = [mean(r) for r in behav.reward_list]
#         n_stays     = [length(r) for r in behav.reward_list]

#         tmp = DataFrame(
#             sub_num     = fill(s, n_planets),
#             true_planet = behav.true_planet,
#             galaxy      = behav.galaxy,
#             prt         = behav.prt,
#             mean_reward = mean_reward,
#             n_stays     = n_stays,
#             alpha       = fill(p.alpha, n_planets),
#             gamma_base  = fill(p.gamma_base, n_planets),
#             gamma_coef  = fill(p.gamma_coef, n_planets),

#         )

#         append!(sim_all, tmp)
#     end

#     CSV.write(save_path, sim_all)
#     println("Saved simulation to: $save_path")

#     return sim_all
# end


# ############################################################
# # 4. ACTUAL CALL (runs when you use `julia script.jl`)
# ############################################################

# if abspath(PROGRAM_FILE) == @__FILE__
#     println("Running structural learning softmax simulation...")
#     simulate_structLearner_softmax(500)
# end



##############################
# simulate_structLearning_softmax.jl
# Self-contained simulation script
##############################

using CSV
using DataFrames
using Random, Distributions
using Statistics
using StatsBase

# load infrastructure
include("./particle_filter.jl")
include("./model_struct.jl")
include("./opt.jl")

# load all helper functions like get_planet, get_galaxy, get_reward, etc.
include("./model.jl")     # <-- make sure this exists and defines Experiment, Behavior, etc.



############################################################
# 1. PARAMETER STRUCT AND SAMPLING FUNCTION
############################################################

struct SLParams
    alpha::Float64       # CRP cluster rate
    gamma_base::Float64
    gamma_coef::Float64
end

function sample_subject_params(n_sub::Int; rng=Random.default_rng())
    dist_gamma_base = Uniform(-10.0, 10.0)
    dist_gamma_coef = Uniform(-3.0, 3.0)
    dist_alpha      = Uniform(0.0, 10.0)

    out = Vector{SLParams}(undef, n_sub)
    for i in 1:n_sub
        out[i] = SLParams(
            rand(rng, dist_alpha),
            rand(rng, dist_gamma_base),
            rand(rng, dist_gamma_coef)
        )
    end
    return out
end


############################################################
# 2. TRIAL-BY-TRIAL LOG STRUCT
############################################################

mutable struct TrialLog
    sub_num::Int
    block::Int
    planet_in_block::Int
    true_planet::Int
    planet::Int
    galaxy::Int
    prt::Int
    stay_num::Int
    reward::Float64
    alpha::Float64
    gamma_base::Float64
    gamma_coef::Float64
end


############################################################
# 3. STRUCTURAL LEARNING MODEL (with trial logging)
############################################################

function crp_adaptiveDiscount_softmax(
    data::DataFrame,
    params::AbstractVector,
    num_particles::Int,
    sub_id::Int
)
    # intialize the exp
    expt = Experiment(5,360,20,2,10,5.5,1.5)
    behav = Behavior([],[],[],[])  # original behavior recorder

    # initialize the particle filter
    alpha       = params[1]
    gamma_base  = params[2]
    gamma_coef  = params[3]

    hyper_mu  = 0.5
    hyper_var = 0.25
    hyper_tau = 1
    n_samples = 100
    particles, weights = init_particle_filter(num_particles, hyper_mu, hyper_var, hyper_tau, alpha)

    # tracking & logs
    total_reward = 0.0
    total_time   = expt.alien_time + expt.iti
    N            = 0    # number of planets experienced
    trial_logs   = TrialLog[]

    n_cluster_inferred = Float64[]
    gammas     = Float64[]
    pred_decay = Float64[]
    uncertainty = Float64[]
    true_decay  = Float64[]
    middle      = Any[]
    middle_decay = Any[]

    for b in 1:expt.n_blocks
        curr_block = data[in(b).(data.block), :]
        b_tracker = Block_Tracker(expt.alien_time, 0)

        planet_idx_in_block = 0

        while (b_tracker.block_time < expt.block_max_time) & (b_tracker.planet < expt.block_n_planet)
            curr_planet, p_tracker = get_planet(b, b_tracker, curr_block)
            planet_idx_in_block += 1
            stay_index = 0

            while (b_tracker.block_time < expt.block_max_time) & p_tracker.on_planet

                # dig up reward and add to list
                p_tracker, total_reward = get_reward(p_tracker, total_reward, curr_planet)
                stay_index += 1

                # --------- TRIAL LOG ENTRY ----------
                # Assuming curr_planet has fields .planet and .galaxy
                push!(trial_logs, TrialLog(
                    sub_id,
                    b,
                    planet_idx_in_block,
                    p_tracker.true_planet,     # SAFE scalar
                    p_tracker.true_planet,     # planet
                    p_tracker.galaxy,          # SAFE scalar
                    p_tracker.prt,
                    stay_index,
                    p_tracker.curr_reward,
                    alpha,
                    gamma_base,
                    gamma_coef
                ))


                # add time that it took to dig it up
                b_tracker.block_time += expt.harvest_time + expt.iti
                total_time += expt.harvest_time + expt.iti

                # probability of cluster
                global prob_k = prob_cluster(p_tracker.curr_reward,
                                             p_tracker.decay_list,
                                             N,
                                             alpha,
                                             particles)
                samples, clusters = sample_v_stay(particles, weights, prob_k, n_samples, p_tracker.decay_list)
                global samples_all = samples

                clusters = round.(Int, clusters)
                K = maximum(clusters)
                append!(n_cluster_inferred, length(prob_k[1]))
                d = Multinomial(n_samples, tally(clusters, K) / n_samples)
                model_uncertainty = entropy(d)
                gamma_effective = 1 / (1 + exp(-(gamma_base - gamma_coef * model_uncertainty)))
                v_stay  = mean(samples) * p_tracker.curr_reward
                v_leave = (total_reward / total_time) * (expt.harvest_time + expt.iti) * gamma_effective
                p_tracker = make_choice_max(v_stay, v_leave, p_tracker)
                append!(middle, [tally(clusters, K)])
                append!(middle_decay, [deepcopy(p_tracker.decay_list)])

            end

            append!(uncertainty, var(samples_all))
            append!(pred_decay, mean(samples_all))
            append!(middle, [[]])
            append!(middle_decay, [[]])

            if p_tracker.prt > 1
                particles, weights = resample_and_update_particles(particles,
                                                                   weights,
                                                                   prob_k,
                                                                   p_tracker.decay_list)
            end

            if p_tracker.prt > 1
                append!(true_decay, mean(p_tracker.decay_list))
            else
                append!(true_decay, 0.0)
            end

            b_tracker.block_time += expt.travel_time + expt.alien_time
            b_tracker.planet     += 1
            total_time           += expt.travel_time + expt.alien_time
            behav = update_behavior(behav, p_tracker)
            N += 1
        end
    end

    return behav, trial_logs
end


############################################################
# 4. SIMULATION WRAPPER
#    Produces:
#    1) all_data_sim_alpha_free.csv  (trial-by-trial)
#    2) ref_point_data_planet_by_planet_sim.csv (planet-level)
############################################################

function simulate_structLearner_softmax(
    n_sub::Int;
    num_particles::Int = 50,
    template_data_path::String = "data/all_data_new.csv",
    save_trial_path::String  = "all_data_sim_alpha_free.csv",
    save_planet_path::String = "ref_point_data_planet_by_planet_sim.csv"
)
    # Load template structure (use the first subject)
    all_data  = DataFrame(CSV.File(template_data_path, delim = ','))
    first_sub = all_data.sub_num[1]
    template  = all_data[in(first_sub).(all_data.sub_num), :]

    # Sample parameters
    param_draws = sample_subject_params(n_sub)

    trial_df  = DataFrame()
    planet_df = DataFrame()

    for s in 1:n_sub
        p = param_draws[s]

        params_vec = [
            p.alpha,
            p.gamma_base,
            p.gamma_coef
        ]

        behav, trial_logs = crp_adaptiveDiscount_softmax(template, params_vec, num_particles, s)

        # ---------- TRIAL-BY-TRIAL: all_data_sim_alpha_free ----------
        trial_df_sub = DataFrame(trial_logs)
        append!(trial_df, trial_df_sub)

        # ---------- PLANET-BY-PLANET: ref_point_data_planet_by_planet_sim ----------
        # Aggregate over each planet within each block
        # group columns: same structure as your example files
        group_cols = [:sub_num, :block, :planet_in_block, :true_planet, :planet, :galaxy]

        planet_df_sub = combine(
            groupby(trial_df_sub, group_cols),
            :prt    => maximum => :prt,
            :reward => mean    => :mean_reward,
            :alpha       => first => :alpha,
            :gamma_base  => first => :gamma_base,
            :gamma_coef  => first => :gamma_coef
        )

        append!(planet_df, planet_df_sub)
    end

    # Save both outputs
    CSV.write(save_trial_path,  trial_df)
    CSV.write(save_planet_path, planet_df)

    println("Saved TRIAL file  → $save_trial_path")
    println("Saved PLANET file → $save_planet_path")

    return trial_df, planet_df
end


############################################################
# 5. ACTUAL CALL (runs when you use `julia script.jl`)
############################################################

if abspath(PROGRAM_FILE) == @__FILE__
    println("Running structural learning softmax simulation...")
    simulate_structLearner_softmax(500)
end
