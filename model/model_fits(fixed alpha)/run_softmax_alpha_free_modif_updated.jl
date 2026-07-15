# run_softmax_alpha_free_modif_updated.jl
#

using Pkg
Pkg.activate(@__DIR__)
Pkg.instantiate()

using Serialization
using CSV, DataFrames
using Random, Distributions
using StatsFuns: logsumexp
using Sobol
using MLBase
using PythonCall
using Printf

Random.seed!(1234)

include(joinpath(@__DIR__, "box_bads.jl"))

# =============================================================================
# Defaults: relative paths only
# =============================================================================

const DEFAULT_OUTPUT_DIR = joinpath(@__DIR__, "softmax")

# Optional metadata CSV. This is NOT needed for fitting; it is only used to recover
# fileID/sub_num for cleaner output. If this file does not exist, the script still runs.
const DEFAULT_DATA_PATH = joinpath(
    @__DIR__,
    "..",
    "generate sim data given alpha star",
    "simulated_structure_learning_RANDOM_1000.csv",
)

# =============================================================================
# Python / PyBADS setup
# =============================================================================

function setup_pybads()
    # Some PyBADS versions can throw a NameError unless Python builtins.D exists.
    # We reset it to the actual parameter dimensionality before every optimization.
    try
        pybuiltins = pyimport("builtins")
        if !pyhasattr(pybuiltins, "D")
            @info "Defining missing Python builtins.D placeholder for PyBADS."
            pybuiltins.D = 1
        end
    catch e
        @warn "Failed to define Python builtins.D placeholder." exception=(e, catch_backtrace())
    end
    pybads = pyimport("pybads")
    return pybads.BADS
end

const BADS = setup_pybads()

# =============================================================================
# Data / metadata helpers
# =============================================================================

normalize_names!(df::DataFrame) = (rename!(df, Pair.(names(df), lowercase.(string.(names(df))))); df)

function parse_subject_id(raw::AbstractString)
    if all(isdigit, raw)
        return parse(Int, raw), :num
    else
        return raw, :fileid
    end
end

function maybe_get_sub_metadata(id, id_type::Symbol, data_path::AbstractString)
    # The model fit itself uses serialized CRP latents. The data CSV is only useful
    # for getting a canonical fileID and sub_num in the output row.
    if !isfile(data_path)
        @warn "Data CSV not found. Continuing without metadata." data_path=data_path
        return (fileID=string(id), sub_num=(id_type == :num ? id : missing))
    end

    df = CSV.read(data_path, DataFrame)
    normalize_names!(df)
    cols = Symbol.(names(df))

    sub_col = :sub_num in cols ? :sub_num :
              (:subject in cols ? :subject :
              (:subject_num in cols ? :subject_num : nothing))

    file_col = :fileid in cols ? :fileid :
               (:file_id in cols ? :file_id :
               (:fileID in cols ? :fileID : nothing))

    if sub_col === nothing && file_col === nothing
        @warn "No subject/fileID column found in metadata CSV. Continuing without metadata." columns=cols
        return (fileID=string(id), sub_num=(id_type == :num ? id : missing))
    end

    if id_type == :num
        if sub_col !== nothing
            subdf = df[df[!, sub_col] .== id, :]
        else
            subdf = df[string.(df[!, file_col]) .== string(id), :]
        end
    else
        if file_col !== nothing
            subdf = df[string.(df[!, file_col]) .== string(id), :]
        else
            subdf = df[string.(df[!, sub_col]) .== string(id), :]
        end
    end

    if nrow(subdf) == 0
        @warn "No rows matched subject in metadata CSV. Continuing without metadata." id=id id_type=id_type
        return (fileID=string(id), sub_num=(id_type == :num ? id : missing))
    end

    fileID = file_col === nothing ? string(id) : string(first(unique(subdf[!, file_col])))
    subnum = sub_col === nothing ? (id_type == :num ? id : missing) : first(unique(subdf[!, sub_col]))

    return (fileID=fileID, sub_num=subnum)
end

function resolve_latents_dir(alpha_level::Integer, latents_arg::Union{Nothing,AbstractString})
    # latents_arg can be either:
    #   A) a direct alpha-specific folder, e.g. crp_latents_alpha_1
    #   B) a root folder containing crp_latents_alpha_1
    if latents_arg === nothing
        return joinpath(@__DIR__, "crp_latents_alpha_$(alpha_level)")
    end

    if basename(normpath(latents_arg)) == "crp_latents_alpha_$(alpha_level)"
        return latents_arg
    end

    nested = joinpath(latents_arg, "crp_latents_alpha_$(alpha_level)")
    return isdir(nested) ? nested : latents_arg
end

function find_latents_path(alpha_level::Integer, id, latents_dir::AbstractString)
    candidates = [
        joinpath(latents_dir, "sub$(id).ser"),
        joinpath(latents_dir, "sub_$(id).ser"),
        joinpath(latents_dir, "$(id).ser"),
    ]

    for p in candidates
        if isfile(p)
            return p
        end
    end

    error("CRP latents not found for id=$(id), alpha=$(alpha_level).\nTried:\n" * join(candidates, "\n"))
end

function get_sub_crp_latents(id, alpha_level::Integer, latents_dir::AbstractString)
    latpath = find_latents_path(alpha_level, id, latents_dir)
    println("Using latents: ", latpath)
    return deserialize(latpath)
end

# =============================================================================
# Model computation
# =============================================================================

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

get_time_constant(action::AbstractString, t::Timing) =
    action == "leave" ? (t.travel + t.alien) : (t.harvest + t.iti)

logmeanexp(x) = logsumexp(x) + log(1 / length(x))

compute_discount_rate(gamma_base, gamma_coef, uncertainty) =
    1 / (1 + exp(-(gamma_base + gamma_coef * uncertainty)))

function get_likelihood(curr_stay_decision, max_stay_decision, v_stay, v_leave, beta, epsilon)
    if curr_stay_decision == max_stay_decision
        # leave decision
        return (1 - epsilon) / (1 + exp(-beta * (v_leave - v_stay))) + (epsilon / 2)
    else
        # stay decision
        return (1 - epsilon) / (1 + exp(-beta * (v_stay - v_leave))) + (epsilon / 2)
    end
end

function compute_likelihood(pred, timing::Timing, gamma_base, gamma_coef, beta, epsilon)
    stay_time = get_time_constant("stay", timing)
    sum_llh = 0.0

    for row in pred
        v_stay = row.pred_reward
        global_rr = row.global_rr
        uncertainty = row.reward_uncert

        gamma_effective = compute_discount_rate(gamma_base, gamma_coef, uncertainty)
        v_leave = global_rr * stay_time * gamma_effective

        curr_stay_num = row.planet_stay_num
        max_stay_num = row.max_planet_stay_num

        likelihood = get_likelihood(
            curr_stay_num,
            max_stay_num,
            v_stay,
            v_leave,
            beta,
            epsilon,
        )

        sum_llh += log(likelihood)
    end

    return sum_llh
end

function model_wrapper(choice_by_choice_predictions, parameters, alpha_level::Integer)
    timing = Timing(3.0, 10.0, 1.5, 5.5)

    if alpha_level == 0
        gamma_base = parameters[1]
        gamma_coef = 0.0
        beta = parameters[2]
        epsilon = parameters[3]
    elseif alpha_level == 1
        gamma_base = parameters[1]
        gamma_coef = parameters[2]
        beta = parameters[3]
        epsilon = parameters[4]
    else
        error("alpha_level must be 0 or 1. Got alpha_level=$(alpha_level).")
    end

    n_runs = length(choice_by_choice_predictions)
    llhs = Vector{Float64}(undef, n_runs)

    for i in 1:n_runs
        llhs[i] = compute_likelihood(
            choice_by_choice_predictions[i],
            timing,
            gamma_base,
            gamma_coef,
            beta,
            epsilon,
        )
    end

    return -logmeanexp(llhs)
end

# =============================================================================
# Optimization
# =============================================================================

function gen_sobol_seq(box, N::Integer)
    xs = collect(Iterators.take(SobolSeq(n_free(box)), N))
    return map(box, xs)
end

function get_parameter_bounds(alpha_level::Integer)
    if alpha_level == 0
        # α = 0 model: γ_base, β, ε
        lb = [-10.0, 0.1, 0.0]
        ub = [ 10.0, 5.0, 0.1]
    elseif alpha_level == 1
        # α* model: γ_base, γ_coef, β, ε
        lb = [-10.0, -3.0, 1, 0.0]
        ub = [ 10.0,  3.0, 1, 0.1]
    else
        error("alpha_level must be 0 or 1. Got alpha_level=$(alpha_level).")
    end

    plb = copy(lb)
    pub = copy(ub)

    if alpha_level == 0
        box = Box(a=(lb[1], ub[1]), b=(lb[2], ub[2]), c=(lb[3], ub[3]))
    else
        box = Box(a=(lb[1], ub[1]), b=(lb[2], ub[2]), c=(lb[3], ub[3]), d=(lb[4], ub[4]))
    end

    return lb, ub, plb, pub, box
end

function run_fit_procedure(choice_by_choice_predictions, alpha_level::Integer; max_iter::Integer=20, convergence_criteria::Integer=4)
    lb, ub, plb, pub, box = get_parameter_bounds(alpha_level)
    init_sobol_seq = gen_sobol_seq(box, 1000)

    best_neg_llh = Inf
    best_params = nothing
    n_nonimproving_starts = 0
    total_starts = 0

    while (n_nonimproving_starts < convergence_criteria) && (total_starts < max_iter)
        init_x = collect(Float64, init_sobol_seq[total_starts + 1])
        D = length(init_x)

        # Ensure PyBADS sees the correct integer dimensionality.
        pyimport("builtins").D = D

        bads_target = x -> model_wrapper(choice_by_choice_predictions, x, alpha_level)

        options = PyDict(Dict(
            "tol_fun" => 1e-4,
            "max_fun_evals" => 1000 * D,
            "specify_target_noise" => false,
        ))

        res = BADS(
            bads_target,
            init_x,
            lb,
            ub,
            plb,
            pub;
            options=options,
        ).optimize()

        neg_llh = pyconvert(Float64, res["fval"])
        x = pyconvert(Vector{Float64}, res["x"])

        if alpha_level == 0
            params = (
                gamma_base = x[1],
                gamma_coef = 0.0,
                beta = x[2],
                epsilon = x[3],
            )
        else
            params = (
                gamma_base = x[1],
                gamma_coef = x[2],
                beta = x[3],
                epsilon = x[4],
            )
        end

        if neg_llh < best_neg_llh
            best_neg_llh = neg_llh
            best_params = params
            n_nonimproving_starts = 0
        else
            n_nonimproving_starts += 1
        end

        total_starts += 1
        @printf("start=%d neg_llh=%.6f best=%.6f nonimproving=%d\n",
                total_starts, neg_llh, best_neg_llh, n_nonimproving_starts)
    end

    best_params === nothing && error("No valid optimization result was produced.")

    return (
        neg_llh = best_neg_llh,
        gamma_base = best_params.gamma_base,
        gamma_coef = best_params.gamma_coef,
        beta = best_params.beta,
        epsilon = best_params.epsilon,
    )
end

# =============================================================================
# Main
# =============================================================================

function main()
    if length(ARGS) < 2
        println("""
        Usage:
          julia run_softmax_alpha_free_modif_updated.jl <alpha_level> <subject_id> [output_dir] [latents_root_or_dir] [data_path]

        Required:
          alpha_level         0 or 1
          subject_id          Numeric sub_num or string fileID

        Optional:
          output_dir          Default: ./softmax
          latents_root_or_dir Default: ./crp_latents_alpha_<alpha_level>
                              Can also be a root folder containing crp_latents_alpha_<alpha_level>.
          data_path           Optional metadata CSV. Not required for fitting.
        """)
        return
    end

    alpha_level = parse(Int, ARGS[1])
    raw_id = ARGS[2]
    id, id_type = parse_subject_id(raw_id)

    output_dir = length(ARGS) >= 3 ? ARGS[3] : DEFAULT_OUTPUT_DIR
    latents_arg = length(ARGS) >= 4 ? ARGS[4] : nothing
    data_path = length(ARGS) >= 5 ? ARGS[5] : DEFAULT_DATA_PATH

    latents_dir = resolve_latents_dir(alpha_level, latents_arg)
    metadata = maybe_get_sub_metadata(id, id_type, data_path)

    println("Running SOFTMAX fit")
    println("  alpha_level = ", alpha_level)
    println("  id_type     = ", id_type)
    println("  id          = ", id)
    println("  output_dir  = ", output_dir)
    println("  latents_dir = ", latents_dir)

    sub_data = get_sub_crp_latents(id, alpha_level, latents_dir)
    result = run_fit_procedure(sub_data, alpha_level)

    outdir = joinpath(output_dir, "neg_llh_alpha_$(alpha_level)")
    mkpath(outdir)

    outcsv = joinpath(outdir, "softmax_alpha$(alpha_level)_$(metadata.fileID).csv")

    final_results = DataFrame([(
        fileID = metadata.fileID,
        sub_num = metadata.sub_num,
        subject_num = string(id),
        neg_llh = Float64(result.neg_llh),
        gamma_base = Float64(result.gamma_base),
        gamma_coef = Float64(result.gamma_coef),
        beta = Float64(result.beta),
        epsilon = Float64(result.epsilon),
    )])

    CSV.write(outcsv, final_results)
    println("Saved → ", outcsv)
end

main()
