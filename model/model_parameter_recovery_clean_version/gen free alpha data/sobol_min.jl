using Sobol
include("./model.jl")
include("./box.jl")

############################################################
# minimize() stays unchanged
############################################################

function minimize(func, samp_points)
    all_loss = Float64[]
    params_tried = Any[]

    for i in 1:length(samp_points)
        params = samp_points[i]
        loss = func(params)
        push!(all_loss, loss)
        push!(params_tried, params)
    end

    min_ind = argmin(all_loss)
    return params_tried[min_ind]
end

############################################################
# UPDATED sobol_min() FOR NEW MODEL (5 parameters)
############################################################

function sobol_min(func, model_num)

    if model_num == 0
        # ==============================
        # STRUCTURAL LEARNING MODEL
        # 5 FREE PARAMETERS:
        # α          ∈ [0, 10]
        # γ_base     ∈ [-10, 10]
        # γ_coef     ∈ [-3,  3]
        # β          ∈ [0.1, 5]
        # ε          ∈ [0, 0.1]
        # ==============================
        box = Box(
            a = (0.0,   10.0),     # alpha
            b = (-10.0, 10.0),     # gamma_base
            c = (-3.0,  3.0),      # gamma_coef
        )

    elseif model_num == 1
        # ------------------------------
        # MVT model (unchanged)
        # ------------------------------
        box = Box(
            a = (0.0, 1.0),    # alpha
            b = (0.0, 20.0),   # beta
            c = (-3.0, 3.0)
        )

    elseif model_num == 2
        # ------------------------------
        # TD model (unchanged)
        # ------------------------------
        box = Box(
            a = (0.0, 1.0),
            b = (0.0, 20.0),
            c = (0.0, 1.0),
            d = (-3.0, 3.0)
        )
    end

    ########################################################
    # Number of Sobol samples (this is grid search, more -> better chance finding optimal)
    ########################################################
    N = 10  # You can increase this to 100+ when needed

    # Generate Sobol points
    xs = Iterators.take(SobolSeq(n_free(box)), N) |> collect
    xs = map(box, xs)

    # Optimize
    return minimize(func, xs)
end
