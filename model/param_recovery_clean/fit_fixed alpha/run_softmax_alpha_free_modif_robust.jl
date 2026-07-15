# run_softmax_alpha_free_modif.jl
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

# === DATA PATH ===============================================================
const DATA_PATH = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\model_parameter_recovery_clean_version\generate sim data given alpha star\simulated_structure_learning_RANDOM_1000.csv"

const LATENTS_DIR = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\model_parameter_recovery_clean_version\fit model to sim data and generate recovery stats\crp_latents_alpha_1"

# === OUTPUT DIR ===============================================================
const SOFTMAX_DIR = joinpath(@__DIR__, "softmax")
isdir(SOFTMAX_DIR) || mkpath(SOFTMAX_DIR)

# === HELPERS ==================================================================
normalize_names!(df::DataFrame) = (rename!(df, Pair.(names(df), lowercase.(string.(names(df))))); df)

function get_sub_data(id; id_type::Symbol)
    df = CSV.read(DATA_PATH, DataFrame)
    normalize_names!(df)
    cols = Symbol.(names(df))

    # detect subject column
    sub_col = :sub_num in cols ? :sub_num :
              (:subject in cols ? :subject : nothing)
    sub_col === nothing && error("No subject column (:sub_num or :subject) found in data. Columns: $(cols)")

    # filter
    out = id_type == :num ? df[df[!, sub_col] .== id, :] :
                            df[df[!, sub_col] .== id, :]
    nrow(out) == 0 && error("No rows found for subject = $id (id_type=$id_type)")

    # detect or create fileid
    file_col = :fileid in cols ? :fileid :
               (:file_id in cols ? :file_id : nothing)
    if file_col === nothing
        out[!, :fileid] = out[!, sub_col]   # fallback
        file_col = :fileid
    end

    # ensure planet_num exists
    cols = Symbol.(names(out))  # refresh
    if :planet_num ∉ cols
        if :planet ∈ cols
            out[!, :planet_num] = out[!, :planet]
        else
            error("Neither :planet_num nor :planet found in subject data. Columns: $(cols)")
        end
    end
    return out
end

function find_latents_path(alpha_level, id)
    candidates = [
        joinpath(LATENTS_DIR, "sub$(id).ser"),
        joinpath(LATENTS_DIR, "sub_$(id).ser"),
        joinpath(LATENTS_DIR, string(id) * ".ser"),
    ]
    for p in candidates
        if isfile(p); return p; end
    end
    error("CRP latents not found for id=$id\nTried:\n" * join(candidates, "\n"))
end

# === MODEL COMPUTATION (unchanged from your version) ==========================
include("box_bads.jl")

struct Timing; harvest::Float64; travel::Float64; iti::Float64; alien::Float64; end
struct Exp; n_blocks::Float64; max_time_in_block::Float64; max_planets_in_block::Float64; end
get_time_constant(action, t::Timing) = action == "leave" ? (t.travel + t.alien) : (t.harvest + t.iti)
logmeanexp(x) = logsumexp(x) + log(1/length(x))
compute_discount_rate(gb,gc,u) = 1/(1+exp(-(gb + gc*u)))

function get_likelihood(curr_stay, max_stay, v_stay, v_leave, beta, epsilon)
    return curr_stay == max_stay ?
        (1-epsilon)/(1+exp(-beta*(v_leave-v_stay))) + (epsilon/2) :
        (1-epsilon)/(1+exp(-beta*(v_stay-v_leave))) + (epsilon/2)
end

function compute_likelihood(pred, t::Timing, gb, gc, beta, epsilon)
    stay_time = get_time_constant("stay", t)
    sum_llh = 0.0
    for row in pred
        v_stay = row.pred_reward
        grr    = row.global_rr
        unc    = row.reward_uncert
        gamma_eff = compute_discount_rate(gb, gc, unc)
        v_leave = grr * stay_time * gamma_eff
        sum_llh += log(get_likelihood(row.planet_stay_num, row.max_planet_stay_num, v_stay, v_leave, beta, epsilon))
    end
    return sum_llh
end

function model_wrapper(pred, θ, αlvl)
    t = Timing(3,10,1.5,5.5); n = length(pred)
    if αlvl==0; gb, beta, eps = θ; gc=0.0
    else; gb, gc, beta, eps = θ; end
    return -logmeanexp([compute_likelihood(pred[i], t, gb, gc, beta, eps) for i in 1:n])
end

function gen_sobol_seq(box,N)
    xs = collect(Iterators.take(SobolSeq(n_free(box)),N))
    map(box, xs)
end

function get_parameter_bounds(alpha_level)
    if alpha_level == 0
        # α = 0 model (no γ_coef)
        lb = [-10.0, 0.1, 0.0]      # γ_base, β, ε lower bounds
        ub = [10.0, 5.0, 0.1]       # γ_base, β, ε upper bounds
    elseif alpha_level == 1
        # α* model (γ_base + γ_coef)
        lb = [-10.0, -3.0, 0.1, 0.0]   # γ_base, γ_coef, β, ε
        ub = [10.0,  3.0,  5.0, 0.1]
    end

    plb = lb
    pub = ub

    if alpha_level == 0
        box = Box(a=(lb[1], ub[1]), b=(lb[2], ub[2]), c=(lb[3], ub[3]))
    elseif alpha_level == 1
        box = Box(a=(lb[1], ub[1]), b=(lb[2], ub[2]), c=(lb[3], ub[3]), d=(lb[4], ub[4]))
    end

    return lb, ub, plb, pub, box
end

function run_fit_procedure(latents, αlvl; max_iter=20, convergence_criteria=4)
    pybads = pyimport("pybads"); BADS = pybads.BADS
    lb,ub,plb,pub,box = get_parameter_bounds(αlvl)
    sob = gen_sobol_seq(box,1000)
    best = (nll=Inf, gb=0.0,gc=0.0,b=0.0,e=0.0)
    nst=0; tot=0
    
    while (nst < convergence_criteria) && (tot < max_iter)

        init = sob[tot+1]; D=length(init)
        (pyimport("builtins")).D = D
        target=x->model_wrapper(latents,x,αlvl)
        opts=PyDict(Dict("tol_fun"=>1e-4,"max_fun_evals"=>1000*D,"specify_target_noise"=>false))
        res=BADS(target,init,lb,ub,plb,pub;options=opts).optimize()
        nll = pyconvert(Float64, res["fval"])
        if nll<best.nll
            x = pyconvert(Vector{Float64}, res["x"])
            if αlvl == 0
                gb, gc, b, e = x[1], 0.0, x[2], x[3]
            else
                gb, gc, b, e = x[1], x[2], x[3], x[4]
            end
                        best=(nll=nll,gb=gb,gc=gc,b=b,e=e); nst=0
        else; nst+=1; end
        tot+=1
    end
    return best
end

# === MAIN ====================================================================
function main()
    if length(ARGS)<2
        println("Usage: julia run_softmax_alpha_free_modif.jl <alpha_level> <subject_id>")
        return
    end

    αlvl=parse(Int,ARGS[1]); raw=ARGS[2]
    id = all(isdigit,raw) ? parse(Int,raw) : raw
    id_type = all(isdigit,raw) ? :num : :fileid

    println("Running SOFTMAX fit for $(id_type==:num ? "sub_num" : "fileID") $id (alpha=$αlvl)")

    subdf = get_sub_data(id; id_type=id_type)
    latpath = find_latents_path(αlvl,id)
    latents = deserialize(latpath)
    println("Using latents: ", latpath)

    result = run_fit_procedure(latents, αlvl)

    outdir = joinpath(SOFTMAX_DIR,"neg_llh_alpha_$(αlvl)")
    isdir(outdir) || mkpath(outdir)

    fileid = string(first(unique(subdf[!,:fileid])))
    subnum = :sub_num in Symbol.(names(subdf)) ? first(unique(subdf[!,:sub_num])) : missing

    outcsv = joinpath(outdir, "softmax_alpha$(αlvl)_$(fileid).csv")
    df = DataFrame([(
        fileID=fileid,
        sub_num=subnum,
        neg_llh=Float64(result.nll),
        gamma_base=Float64(result.gb),
        gamma_coef=Float64(result.gc),
        beta=Float64(result.b),
        epsilon=Float64(result.e)
    )])
    CSV.write(outcsv,df)
    println("Saved → ", outcsv)
end

main()






