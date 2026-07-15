using JLD

include("./model_with_beta_and_epsilon.jl")
include("./opt.jl")
include("./sobol_min.jl")

function get_sub_ref_point(sub_num)
    #all_data=DataFrame(CSV.File("data/ref_point_data_planet_by_planet_dataset_2022.csv",delim=','))
    #all_data=DataFrame(CSV.File("data/all_data_by_planet_new.csv",delim=','))
    all_data = DataFrame(CSV.File("data/all_data_by_planet_online_final.csv"))
    sub_data = all_data[in(sub_num).(all_data.sub_num),:] 

    return sub_data
end

function get_block(true_planet)
    block =[]
    for p in true_planet
        if p < 20
            append!(block,1)
        elseif p < 40
            append!(block,2)
        elseif p < 60
            append!(block,3)
        elseif p < 80
            append!(block,4)
        elseif p < 100
            append!(block,5)
        end
    end
    return block
end

# function package_results(behavior)
#     opt_prt = optimal_policy(behavior)
#     diff = behavior.prt - opt_prt

#     # put in dataframe and save
#     df = DataFrame(Dict("true_planet"=> behavior.true_planet,"block"=> get_block(behavior.true_planet),"galaxy"=> behavior.galaxy,"prt"=>behavior.prt,
#         "opt_prt"=>opt_prt, "diff" => diff))

#     gdf = groupby(df, :true_planet)
#     prt_avg = combine(gdf, :prt => mean)
#     return prt_avg
# end

function package_results(behavior)
    # We can still call optimal_policy if you want to keep it for debugging,
    # but we no longer use it in the returned summary.
    # opt_prt = optimal_policy(behavior)

    # Build a planet-level DataFrame from the behavior object
    df = DataFrame(
        true_planet = behavior.true_planet,
        block       = get_block(behavior.true_planet),
        galaxy      = behavior.galaxy,
        prt         = behavior.prt,
        # opt_prt   = opt_prt,       # not needed for fitting
        # diff      = behavior.prt .- opt_prt  # REMOVE: causes DimensionMismatch
    )

    # Average prt by true_planet (this is what return_loss uses)
    gdf    = groupby(df, :true_planet)
    prt_avg = combine(gdf, :prt => mean)

    return prt_avg
end



function return_loss(behavior,ref_points)
    prt_avg = package_results(behavior)
    planets = ref_points.true_planet

    sse = 0
    n_datapoints = 0
    for p in planets
        pred = prt_avg[(prt_avg[!,"true_planet"].==p),:].prt_mean
        target = ref_points[(ref_points[!,"true_planet"].==p),:].prt

        if (length(pred) > 0) & (length(target) > 0)
            error = (pred[1] - target[1])^2
            sse += error
            n_datapoints += 1
        end

    end
    return sse/n_datapoints
end

function loss_function_crp(params,n_sims=25,num_particles=1)
    sub_num = parse(Int64,ARGS[1])

    sub_data = get_sub_data(sub_num)
    sub_ref_points = get_sub_ref_point(sub_num)
    all_sse = 0
    for i in 1:n_sims
        b = crp_adaptiveDiscount(sub_data,params,num_particles)
        all_sse += return_loss(b,sub_ref_points)
    end
    return all_sse/n_sims
end



function loss_function_mvt(params,n_sims=25)
    sub_num = parse(Int64,ARGS[1])

    sub_data = get_sub_data(sub_num)
    sub_ref_points = get_sub_ref_point(sub_num)
    all_sse = 0
    for i in 1:n_sims
        b = MVT_learn(sub_data,params)
        all_sse += return_loss(b,sub_ref_points)
    end
    return all_sse/n_sims
end

function loss_function_td(params,n_sims=25)
    sub_num = parse(Int64,ARGS[1])

    sub_data = get_sub_data(sub_num)
    sub_ref_points = get_sub_ref_point(sub_num)
    all_sse = 0
    for i in 1:n_sims
        b = TD(sub_data,params)
        all_sse += return_loss(b,sub_ref_points)
    end
    return all_sse/n_sims
end



function opt_params(model_num)
    println("start opt")
    if model_num == 0
        res = sobol_min(loss_function_crp, model_num)
    elseif model_num == 1
        res = sobol_min(loss_function_mvt, model_num)
    elseif model_num == 2
        res = sobol_min(loss_function_td, model_num)
    end
    return res
end

function main()
    sub_num = parse(Int64,ARGS[1])
    model_num = parse(Int64,ARGS[2])

    result = opt_params(model_num)
    println(result)
    if model_num == 0
        save(string("fit_params/adaptive_discount_all_with_beta_and_epsilon/sub",string(sub_num),".jld"), "res", result)
    elseif model_num == 1
        save(string("fit_params/MVT_learn_1_20_3/sub",string(sub_num),".jld"), "res", result)
    elseif model_num == 2
        save(string("fit_params/td_1_20_1_3/sub",string(sub_num),".jld"), "res", result)
    end
end

#main()


# Only run main() if this file is executed directly:
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end