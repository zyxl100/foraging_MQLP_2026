using Serialization
using CSV, DataFrames
using StatsFuns: logistic, logsumexp
using Random, Distributions
using Sobol
using MLBase
using PythonCall
using PythonCall: pyconvert

# fit_moving_window.jl
# Sliding-window parameter reliability per subject, joined with age.
# ---------- Helpers copied from your modif fitter ----------
struct Timing; harvest::Float64; travel::Float64; iti::Float64; alien::Float64; end
struct Exp; n_blocks::Float64; max_time_in_block::Float64; max_planets_in_block::Float64; end

function get_time_constant(action::AbstractString, t::Timing)
    action == "leave" ? (t.travel + t.alien) : (t.harvest + t.iti)
end

logmeanexp(x) = logsumexp(x) - log(length(x))

function get_likelihood(curr_stay_decision, max_stay_decision, v_stay, v_leave, beta, epsilon)
    if curr_stay_decision == max_stay_decision # leave
        (1-epsilon)/(1+exp(-beta*(v_leave-v_stay))) + (epsilon/2)
    else
        (1-epsilon)/(1+exp(-beta*(v_stay-v_leave))) + (epsilon/2)
    end
end

compute_discount_rate(g_base, g_coef, u) = 1 / (1 + exp(-(g_base + g_coef*u)))

function compute_likelihood(pred_window, timing::Timing, gamma_base, gamma_coef, beta, epsilon)
    stay_time = get_time_constant("stay", timing)
    s = 0.0
    @inbounds for r in pred_window
        v_stay = r.pred_reward
        gamma_eff = compute_discount_rate(gamma_base, gamma_coef, r.reward_uncert)
        v_leave = r.global_rr * stay_time * gamma_eff
        p = get_likelihood(r.planet_stay_num, r.max_planet_stay_num, v_stay, v_leave, beta, epsilon)
        s += log(p)
    end
    return s
end

function model_wrapper(choice_by_choice_predictions::Vector, θ::Vector{Float64}, alpha_level::Int)
    timing = Timing(3,10,1.5,5.5)  # same constants as modif script
    gamma_base, gamma_coef, beta, epsilon =
        alpha_level == 0 ? (θ[1], 0.0, θ[2], θ[3]) : (θ[1], θ[2], θ[3], θ[4])

    n_runs = length(choice_by_choice_predictions)
    buf = Vector{Float64}(undef, n_runs)
    # average log-likelihood across Monte-Carlo runs (robust to latent noise)
    @inbounds for i in 1:n_runs
        buf[i] = compute_likelihood(choice_by_choice_predictions[i], timing, gamma_base, gamma_coef, beta, epsilon)
    end
    return -logmeanexp(buf)  # negative LLH objective
end

# Bounds identical to your modif fitter (note: α=1 has γ_coef in [-3,0])
# Return only numeric bounds; we'll sample Sobol in [0,1]^D and affine-map to bounds
function get_parameter_bounds(alpha_level::Int)
    if alpha_level == 0
        lb = [-10.0, 0.0, 0.0]     # [γ_base, β, ε]
        ub = [ 10.0, 1.0, 1.0]
    else
        lb = [-10.0, -3.0, 0.0, 0.0]   # [γ_base, γ_coef, β, ε]
        ub = [ 10.0,  0.0, 1.0, 1.0]
    end
    return lb, ub
end

# Generate N Sobol initial points uniformly inside the [lb, ub] box
function sobol_inits(lb::Vector{<:Real}, ub::Vector{<:Real}, N::Int)
    D = length(lb)
    seq = collect(Iterators.take(SobolSeq(D), N))  # points z in (0,1)^D
    inits = Vector{Vector{Float64}}(undef, N)
    @inbounds for i in 1:N
        z = seq[i]
        x = Vector{Float64}(undef, D)
        for d in 1:D
            x[d] = lb[d] + (ub[d] - lb[d]) * z[d]
        end
        inits[i] = x
    end
    return inits
end


function run_fit_procedure(subject_window_latents::Vector, alpha_level::Int; max_iter::Int=20, convergence_criteria::Int=4)
    Random.seed!(1234)
    pybads = pyimport("pybads"); BADS = pybads.BADS
    pyos = pyimport("os")
    pyos.environ["PYBADS_OPTIONS_FILE"] = ""   # disable external options files
    np = pyimport("numpy")

    # bounds
    lb, ub = get_parameter_bounds(alpha_level)
    rng = ub .- lb
    # set plausible bounds (strictly inside hard bounds to avoid TooCloseBounds)
    plb = lb .+ 1e-3 .* rng
    pub = ub .- 1e-3 .* rng

    # Sobol inits in the hard box
    init_sobol = sobol_inits(lb, ub, max_iter)

    best_neg = Inf
    best_params = nothing
    n_stale = 0
    total = 0

    while (n_stale < convergence_criteria) & (total < max_iter)
        total += 1
        x0 = init_sobol[total]
        D = length(x0)

        # make D visible to pybads option expressions
        pyimport("builtins").D = D

        x0_np  = np.array(x0;  dtype=np.float64)
        lb_np  = np.array(lb;  dtype=np.float64)
        ub_np  = np.array(ub;  dtype=np.float64)
        plb_np = np.array(plb; dtype=np.float64)
        pub_np = np.array(pub; dtype=np.float64)

        bads_target = x -> model_wrapper(subject_window_latents, pyconvert(Vector{Float64}, x), alpha_level)

        opts = PyDict(Dict(
            "tol_fun" => 1e-4,
            "max_fun_evals" => 1000*D,
            "specify_target_noise" => false
        ))

        bads = BADS(bads_target, x0_np, lb_np, ub_np, plb_np, pub_np; options=opts)
        res = bads.optimize()

        # Convert Python objects -> Julia
        neg   = pyconvert(Float64, res["fval"])
        xbest = pyconvert(Vector{Float64}, res["x"])  # Julia is 1-based indexing

        if alpha_level == 0
            params = (γb = xbest[1], γc = 0.0,  β = xbest[2], ε = xbest[3])
        else
            params = (γb = xbest[1], γc = xbest[2], β = xbest[3], ε = xbest[4])
        end
        

        if neg < best_neg
            best_neg = neg
            best_params = params
            n_stale = 0
        else
            n_stale += 1
        end
    end

    return best_neg, best_params.γb, best_params.γc, best_params.β, best_params.ε
end


# ---------- Moving window utilities ----------
# Slice each Monte-Carlo run to [i:j] choice indices; skip if out-of-range.

function slice_latents(latents::Vector, i::Int, j::Int)
    out = Vector{Vector{NamedTuple}}()
    for r in latents
        if j <= length(r)
            push!(out, r[i:j])  # simple slice; no @view
        end
    end
    return out
end


# For one subject: walk windows and fit params per window.
function fit_subject_windows(sub_num::Int, alpha_level::Int; window_len::Int=100, step::Int=25, latents_dir::AbstractString="crp_latents_alpha_")
    file = "$(latents_dir)$(alpha_level)/sub$(sub_num).ser"
    latents = deserialize(file)
    n_choices = length(latents[1])  # assume all runs same length

    starts = collect(1:step:max(1, n_choices - window_len + 1))
    rows = DataFrame(subject_num=Int[], alpha_level=Int[], win_start=Int[], win_end=Int[],
                     neg_llh=Float64[], gamma_base=Float64[], gamma_coef=Float64[],
                     beta=Float64[], epsilon=Float64[])

    for s in starts
        e = s + window_len - 1
        # drop window if it would be too short across many runs
        wlat = slice_latents(latents, s, min(e, n_choices))
        if length(wlat) == 0 || length(wlat[1]) < max(5, Int(0.1*window_len))  # sanity: at least 5 trials
            continue
        end
        neg, γb, γc, β, ε = run_fit_procedure(wlat, alpha_level)
        push!(rows, (sub_num, alpha_level, s, min(e, n_choices), neg, γb, γc, β, ε))
    end
    return rows
end

# ---------- Batch pipeline over subjects with age join ----------
"""
main(args):
  ARGS[1] = alpha_level (0 or 1)
  ARGS[2] = window_len  (e.g., 80)
  ARGS[3] = step        (e.g., 20)
  ARGS[4] = ages_csv    (e.g., ./data/sub_ages_20240417.csv)
  ARGS[5] = out_csv     (e.g., ./moving_window_alpha0.csv)
  Optional: ARGS[6] = subjects_csv to limit to a list; otherwise inferred from available .ser files.
"""
function main()
    alpha_level = parse(Int, ARGS[1])
    window_len  = parse(Int, ARGS[2])
    step        = parse(Int, ARGS[3])
    ages_csv    = ARGS[4]
    out_csv     = ARGS[5]

    dirpath = "crp_latents_alpha_$(alpha_level)"
    files = readdir(dirpath; join=true)
    subjects = Int[]
    for f in files
        b = basename(f)
        m = match(r"^sub(\d+)\.ser$", b)
        m === nothing && continue
        push!(subjects, parse(Int, m.captures[1]))
    end
    subjects = sort(unique(subjects))


    # optional restriction file (one column 'sub_num')
    if length(ARGS) >= 6
        sublist = CSV.read(ARGS[6], DataFrame)
        subjects = intersect(subjects, sort(collect(sublist.sub_num)))
    end

    ages = CSV.read(ages_csv, DataFrame; normalizenames=true)

    # Normalize headers: lowercase, trim leading junk (incl. BOM), collapse non-alnum to underscores
    old = names(ages)
    norm = Symbol.(replace.(lowercase.(string.(old)),
                            r"^\W+" => "",          # drop leading non-alnum (BOM, spaces)
                            r"[^a-z0-9]+" => "_"))  # collapse everything else to "_"
    rename!(ages, Dict(old .=> norm))

    # Accepted names
    sub_candidates = [:sub_num, :subject_num, :subject, :sub, :id]
    age_candidates = [:age, :age_years, :years, :age_in_years]

    # Pick first that exists (no default= keyword; use isempty ? nothing : list[1])
    sub_matches = [c for c in sub_candidates if c in names(ages)]
    age_matches = [c for c in age_candidates if c in names(ages)]

    sub_sym = isempty(sub_matches) ? nothing : sub_matches[1]
    age_sym = isempty(age_matches) ? nothing : age_matches[1]

    # Fallbacks: if still missing, use col 1 for subject id, col 2 for age (if present)
    if sub_sym === nothing
        if ncol(ages) >= 1
            sub_sym = names(ages)[1]
        else
            error("Ages CSV needs a subject id column; put it in column 1 or name it like one of: $(sub_candidates)")
        end
    end
    if age_sym === nothing && ncol(ages) >= 2
        age_sym = names(ages)[2]
    end

    # Build age map (allow missing ages)
    age_map = Dict(row[sub_sym] => (age_sym === nothing ? missing : row[age_sym]) for row in eachrow(ages))




    all = DataFrame()
    for s in subjects
        println("Fitting subject $s (alpha=$alpha_level) with window_len=$window_len, step=$step")
        rows = fit_subject_windows(s, alpha_level; window_len=window_len, step=step)
        if :age in names(ages)
            rows.age = get(age_map, s, missing)
        end
        all = vcat(all, rows; cols=:union)
    end

    mkpath(dirname(out_csv))
    CSV.write(out_csv, all)
    println("Saved: $(out_csv)")
end

main()
