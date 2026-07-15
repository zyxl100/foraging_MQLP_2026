using Serialization 
using StatsFuns: logistic, logsumexp
using CSV
using DataFrames
using Random, Distributions
using Sobol
using MLBase
using PythonCall

include("box_bads.jl")

Random.seed!(1234) # set random seed 
pybads = pyimport("pybads")
BADS = pybads.BADS

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

function get_time_constant(action, timing_struct)
    if action == "leave"
        return timing_struct.travel + timing_struct.alien 
    else
        return timing_struct.harvest + timing_struct.iti
    end
end

###############################################################################################
# Helper functions 

function logmeanexp(x)
    logsumexp(x) + log(1/length(x))
end

function transform_beta(y,lower_bound,upper_bound)
    #https://en.wikipedia.org/wiki/Beta_distribution
    return (y-lower_bound)/(upper_bound-lower_bound)
end

###############################################################################################

function get_likelihood(curr_stay_decision, max_stay_decision, v_stay, v_leave, beta, epsilon)
    if curr_stay_decision == max_stay_decision # leave decision 
        return (1-epsilon)/(1+exp(-beta*(v_leave-v_stay))) + (epsilon/2)
    else 
        return (1-epsilon)/(1+exp(-beta*(v_stay-v_leave))) + (epsilon/2)
    end 
end

function compute_discount_rate(g_base,g_coef,u)
    return 1/(1+exp(-(g_base + g_coef*u)))

end

###############################################################################################

function compute_likelihood(pred, timing, gamma_base, gamma_coef, beta, epsilon)    
    # fixed parameters
    stay_time = get_time_constant("stay", timing)

    n_choices = length(pred)
    sum_llh = 0
    for choice = 1:n_choices
        # model estimates 
        v_stay = pred[choice].pred_reward
        
        global_rr = pred[choice].global_rr
        uncertainty = pred[choice].reward_uncert
        gamma_effective = compute_discount_rate(gamma_base, gamma_coef, uncertainty)
        v_leave = global_rr*stay_time*gamma_effective
        
        # observed 
        curr_stay_num = pred[choice].planet_stay_num
        max_stay_num = pred[choice].max_planet_stay_num
        this_choice_likelihood = get_likelihood(curr_stay_num, max_stay_num, v_stay, v_leave, beta, epsilon)
        sum_llh += log(this_choice_likelihood)
    end 
    return sum_llh 
end
###############################################################################################
function model_wrapper(choice_by_choice_predictions, parameters, alpha_level)
    exp_struc = Exp(4,360,20) # number of blocks, max time in block, max number of planets visited in block 
    exp_timing = Timing(3,10,1.5,5.5) # harvest time, travel time, iti, alien time 
    if alpha_level == 0
        gamma_base = parameters[1]
        gamma_coef = 0
        beta = parameters[2]
        epsilon = parameters[3]
    elseif alpha_level == 1
        gamma_base = parameters[1]
        gamma_coef = parameters[2]
        beta = parameters[3]
        epsilon = parameters[4]
    end 
    n_runs = length(choice_by_choice_predictions)
    return -logmeanexp(map!(p->compute_likelihood(choice_by_choice_predictions[p], exp_timing, gamma_base, gamma_coef, beta, epsilon), zeros(Float64, n_runs), 1:n_runs))
end

function gen_sobol_seq(box,N)
    xs = Iterators.take(SobolSeq(n_free(box)), N) |> collect
    xs=map(box, xs);
end

function get_parameter_bounds(alpha_level)
    if alpha_level == 0
        lb = [-10.0, 0, 0]
        ub = [10.0, 1.0, 1.0]
    elseif alpha_level == 1
        lb = [-10.0, -3.0, 0, 0]
        ub = [10.0, 3.0, 1.0, 1.0]
    end 
    plb = lb 
    pub = ub 
    if alpha_level == 0
        box = Box( a = (lb[1],ub[1]), b = (lb[2],ub[2]), c = (lb[3],ub[3]))
    elseif alpha_level == 1
        box = Box( a = (lb[1],ub[1]), b = (lb[2],ub[2]), c = (lb[3],ub[3]), d = (lb[4],ub[4]))
    end 
    return lb, ub, plb, pub, box
end  

function run_fit_procedure(subject_data, alpha_level, max_iter=20, convergence_criteria=4)

    # sample from a sobol sequence to get various initial values
    n_starts = 0
    total_starts = 0
    best_neg_llh = 100000
    best_params =  nothing
    lb, ub, plb, pub, box = get_parameter_bounds(alpha_level)
    init_sobol_seq = gen_sobol_seq(box, 1000)

    # sample from a sobol sequence to get various initial values
    while (n_starts < convergence_criteria) & (total_starts < max_iter)
        init_seq = init_sobol_seq[total_starts + 1]
        if alpha_level == 0
            init_x = [init_seq[1], init_seq[2], init_seq[3]]
        elseif alpha_level == 1
            init_x = [init_seq[1], init_seq[2], init_seq[3], init_seq[4]]
        end 
        bads_target = (x) -> model_wrapper(subject_data, x, alpha_level)
        options = Dict("tol_fun"=> 1.0, "max_fun_evals"=>1000, "specify_target_noise"=>false)
        bads = BADS(bads_target, init_x, lb, ub, plb, pub, options=options)
        res = bads.optimize()

        neg_llh = res["fval"]
        if alpha_level == 0
            gamma_base = res["x"][0]
            gamma_coef = 0
            beta = res["x"][1]
            epsilon = res["x"][2]
        elseif alpha_level == 1
            gamma_base = res["x"][0]
            gamma_coef = res["x"][1]
            beta = res["x"][2]
            epsilon = res["x"][3]
        end 
        best_params = (gamma_base=gamma_base, gamma_coef=gamma_coef,beta=beta,epsilon=epsilon)

        if pyconvert(Float64, neg_llh) < pyconvert(Float64, best_neg_llh)
            best_neg_llh = neg_llh
            n_starts = 0
        else
            n_starts += 1
        end
        total_starts += 1
        println("total starts: ")
        println(total_starts)
    end
    best_gamma_base = best_params.gamma_base
    best_gamma_coef = best_params.gamma_coef
    best_beta = best_params.beta
    best_epsilon = best_params.epsilon
    return pyconvert(Vector{Float64},[best_neg_llh, best_gamma_base, best_gamma_coef, best_beta,best_epsilon])
end

function get_sub_crp_latents(sub_num,alpha_level)
    return deserialize("crp_latents_alpha_"*string(alpha_level)*"/sub"*string(sub_num)*".ser")
end 

function main()
    alpha_level = parse(Int64,ARGS[1])
    sub_num = parse(Int64,ARGS[2])
    sub_data = get_sub_crp_latents(sub_num, alpha_level)

    res = run_fit_procedure(sub_data,alpha_level)
    final_results = DataFrame("subject_num"=>sub_num, "neg_llh"=>res[1],"gamma_base"=>res[2],"gamma_coef"=>res[3],"beta"=>res[4],"epsilon"=>res[5])
    file_name = string("softmax/neg_llh_alpha_"*string(alpha_level)*"/sub"*string(sub_num)*".csv")
    CSV.write(file_name,final_results)
end

main()