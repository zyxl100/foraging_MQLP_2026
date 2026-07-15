function crp_adaptiveDiscount(exp_struc,params,num_particles,beta_paras)
    # intialize the exp
    expt = Experiment(5,360,20,2,10,5.5,1.5) # change needed if we want to manipulate the time
    behav = Behavior([],[],[],[])   # true_planet, prt, galaxy, reward_lst

    # initialize the particle filter
    alpha = params[1]
    gamma_base = params[2]
    gamma_coef = params[3]
    #println(params)
    hyper_mu = 0.5
    hyper_var = 0.25
    hyper_tau = 1
    n_samples = 100
    particles, weights = init_particle_filter(num_particles,hyper_mu, hyper_var, hyper_tau, alpha)

    # initialize for tracking progress through the exp
    total_reward = 0
    total_time = expt.alien_time + expt.iti
    N = 0 # all planets experienced, ***check if changes if I change to number of decay rates ***
    n_cluster_inferred = []
    gammas = []
    pred_decay = []
    uncertainty=[]
    true_decay=[]
    middle = []
    middle_decay = []
    true_decay_lst = []
    true_galaxy_lst = []
    rewards = []
    m_uncertainty = []  # YC added, 11-30-23
    for b in 1:expt.n_blocks    # go throught each block?
        curr_block = exp_struc[in(b).(exp_struc.block),:]   # data for the current block
        b_tracker = Block_Tracker(expt.alien_time,0) # block time, planet (current planet num?)
        while (b_tracker.block_time < expt.block_max_time) & (b_tracker.planet < expt.block_n_planet) # while within time limit + do NOT exceed the max planet num (20 for now)
            curr_planet, p_tracker = get_planet(b, b_tracker,curr_block,exp_struc)
            curr_m_uncertainty = [] # YC added, 11-30-23
            while (b_tracker.block_time < expt.block_max_time) & p_tracker.on_planet

                # dig up reward and add to list
                p_tracker, total_reward = get_reward(p_tracker, total_reward, curr_planet, beta_paras)

                # add time that it took to dig it up
                b_tracker.block_time += expt.harvest_time + expt.iti
                total_time += expt.harvest_time + expt.iti

                # probability of cluster
                global prob_k = prob_cluster(p_tracker.curr_reward, p_tracker.decay_list, N, alpha, particles)
                samples,clusters = sample_v_stay(particles,weights, prob_k, n_samples,p_tracker.decay_list)
                global samples_all = samples

                clusters = round.(Int, clusters)
                K = maximum(clusters)
                append!(n_cluster_inferred,length(prob_k[1]))
                d =Multinomial(n_samples,tally(clusters,K)/n_samples)
                model_uncertainty = entropy(d)
                gamma_effective = 1/(1+exp(-(gamma_base - gamma_coef*model_uncertainty)))
                v_stay = mean(samples)*p_tracker.curr_reward
                v_leave = (total_reward/total_time)*(expt.harvest_time + expt.iti)*gamma_effective
                p_tracker =  make_choice_max(v_stay, v_leave, p_tracker)
                append!(middle,[tally(clusters,K)])
                append!(middle_decay,[deepcopy(p_tracker.decay_list)])
                append!(rewards, total_reward)  # YC added, 11-23
                append!(curr_m_uncertainty, model_uncertainty)
            end
            append!(uncertainty,var(samples_all))
            append!(pred_decay,mean(samples_all))
            append!(middle,[[]])
            append!(middle_decay,[[]])
            append!(m_uncertainty, mean(curr_m_uncertainty))    # YC added, 11-30-23

            if p_tracker.prt > 1
                particles, weights = resample_and_update_particles(particles,weights,prob_k,p_tracker.decay_list)
            end

            if p_tracker.prt > 1
                append!(true_decay,mean(p_tracker.decay_list))
                append!(true_decay_lst, p_tracker.decay_list)
                append!(true_galaxy_lst, repeat([p_tracker.galaxy], length(p_tracker.decay_list)))
                for idx in 2:length(p_tracker.reward_list)
                    dd = round(p_tracker.decay_list[idx-1], digits=3)
                    old_r = p_tracker.reward_list[idx-1]
                    new_r = p_tracker.reward_list[idx]
                    actual_dd = round(new_r/old_r, digits=3)
                    if abs(actual_dd-dd)>0.1
                        println("!!!")
                        println(dd, " ", actual_dd)
                    end
                end
            else
                append!(true_decay,0)
            end
            b_tracker.block_time += expt.travel_time + expt.alien_time
            b_tracker.planet += 1
            total_time += expt.travel_time + expt.alien_time
            behav = update_behavior(behav, p_tracker)
            N += 1
            # println(N-1, " DONE, on block ", b, " galaxy ", behav.galaxy)

        end
    end
    true_decay_lst = filter(x -> !isnan(x), true_decay_lst)
    true_galaxy_lst = filter(x -> !isnan(x), true_galaxy_lst)
    # println(mean(vars)^0.5)
    return behav, pred_decay, uncertainty, true_decay, true_decay_lst, true_galaxy_lst, rewards, m_uncertainty
end