using Distributions
using Serialization

include("gen_crp_softmax.jl")

function explore_parameter_space(alpha, n_samples=1000)

    # Generate 1000 random parameter combinations
    gamma_base_bounds = (-10, 10) 
    gamma_coef_bounds = (-3, 3)
    beta_bounds = (0, 1)

    n_samples = 1000
    results = []

    for i in 1:n_samples
        println("sample: ", i)
        # Sample parameters uniformly from bounds
        alpha = alpha
        gamma_base = rand() * (gamma_base_bounds[2] - gamma_base_bounds[1]) + gamma_base_bounds[1]
        gamma_coef = 0
        beta = rand() * (beta_bounds[2] - beta_bounds[1]) + beta_bounds[1]
        
        # Run model with sampled parameters
        simulated_data, max_clus, total_reward = crp([alpha, gamma_base, gamma_coef, beta])
        push!(results, (alpha=alpha, gamma_base=gamma_base, gamma_coef=gamma_coef, beta=beta, max_clus=max_clus, total_reward=total_reward))
    end
    return results
end

function main()
    alpha_level = parse(Float64,ARGS[1])
    alpha = 0.1 + 0.1*alpha_level

    println("Running with alpha = ", alpha)
    results = explore_parameter_space(alpha)
    
    serialize(string("results/equate_total_reward/parameter_space_results_alpha_",string(alpha),".ser"), results)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end