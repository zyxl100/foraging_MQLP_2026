using CSV, DataFrames, JLD, Random, Distributions
using Glob

# =========================================================
# >>>> EDIT THESE TWO PATHS ONLY <<<<
# =========================================================

FITS_DIR = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\fit_params\adaptive_discount_all_with_beta_and_epsilon"

OUT_CSV  = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\nll_outputs\ALL_SUBJECTS_NLL.csv"

mkpath(dirname(OUT_CSV))

# =========================================================
# Load your model + helpers (same ones used for fitting)
# =========================================================

include("fit_by_planet.jl")
include("model_struct.jl")
include("model_with_beta_and_epsilon.jl")

# =========================================================
# Bernoulli Negative Log Likelihood
# =========================================================

function negloglik_bernoulli(p, c)
    p = clamp(p, 1e-6, 1 - 1e-6)
    return c == 1 ? -log(p) : -log(1 - p)
end

# =========================================================
# Simulate once and compute NLL
# =========================================================

function simulate_and_nll(sub_num, params)
    data = get_sub_data(sub_num)

    b = crp_adaptiveDiscount(data, params, 1)

    nll = 0.0
    for t in eachindex(b.p_stay_list)
        nll += negloglik_bernoulli(b.p_stay_list[t], b.choice_list[t])
    end
    return nll
end

# =========================================================
# MAIN BATCH LOOP (NO ARGS USED ✅)
# =========================================================

println("✅ Scanning fitted JLD files...")
files = glob("sub*.jld", FITS_DIR)

@assert length(files) > 0 "❌ No JLD files found in FITS_DIR"

all_rows = DataFrame(sub = Int[], sim = Int[], nll = Float64[])

for file in files
    fname = basename(file)
    sub = parse(Int, replace(fname, r"sub|\.jld" => ""))

    println("▶ Processing subject ", sub)

    try
        d = load(file)
        @assert haskey(d, "res") "Missing key 'res'"
        params = d["res"]

        for sim_id in 1:50
            nll = simulate_and_nll(sub, params)
            push!(all_rows, (sub=sub, sim=sim_id, nll=nll))
        end

    catch err
        println("⚠️ SKIPPING SUBJECT $sub due to error:")
        println(err)
        continue   # ✅ THIS IS THE IMPORTANT LINE
    end
end


CSV.write(OUT_CSV, all_rows)

println("\n✅✅✅ DONE")
println("Saved to:")
println(OUT_CSV)
