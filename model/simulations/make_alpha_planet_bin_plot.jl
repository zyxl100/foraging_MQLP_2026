using Distributed
using Serialization
using Statistics
using Printf

# -------------------------------------------------------------------
# Includes (use your existing code)
# -------------------------------------------------------------------
include("gen_crp_softmax.jl")    # defines crp(params)         :contentReference[oaicite:2]{index=2}
include("find_best_alpha.jl")    # defines explore_parameter_space(alpha; n_samples) :contentReference[oaicite:3]{index=3}

# -------------------------------------------------------------------
# Settings
# -------------------------------------------------------------------
const OUTDIR  = get(ENV, "OUTDIR", "results_alpha_bins")
mkpath(OUTDIR)

# Alpha grid + simulation count
const ALPHAS  = 0.0:0.1:10.0
const N_SIMS  = parse(Int, get(ENV, "N_SIMS", "100"))

# Parallel workers (optional)
# If you are on SLURM, set SLURM_CPUS_PER_TASK; otherwise default to 8.
const NPROCS  = parse(Int, get(ENV, "SLURM_CPUS_PER_TASK", "8"))

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
"""
Return the mode of an Int vector.
If there is a tie, returns the smallest value among the tied modes.
"""
function int_mode(x::Vector{Int})
    counts = Dict{Int, Int}()
    for v in x
        counts[v] = get(counts, v, 0) + 1
    end
    maxc = maximum(values(counts))
    modes = sort([k for (k, c) in counts if c == maxc])
    return modes[1]
end

"""
Summarize a single alpha:
- sim many times (other params drawn from priors inside explore_parameter_space)
- return histogram + mode + mean/var for max_clus
"""
function summarize_alpha(alpha::Float64; n_sims::Int=N_SIMS)
    sims = explore_parameter_space(alpha; n_samples=n_sims)

    max_clus_vec = [s.max_clus for s in sims]  # "recovered planets" per sim
    planet_mode  = int_mode(max_clus_vec)
    planet_mean  = mean(max_clus_vec)
    planet_var   = var(max_clus_vec)

    # histogram as Dict{Int,Int}
    hist = Dict{Int,Int}()
    for k in max_clus_vec
        hist[k] = get(hist, 0) + 1
    end

    return (alpha=alpha,
            planet_mode=planet_mode,
            planet_mean=planet_mean,
            planet_var=planet_var,
            planet_hist=hist)
end

# -------------------------------------------------------------------
# Parallel setup (safe for local + cluster)
# -------------------------------------------------------------------
if nprocs() == 1
    addprocs(NPROCS)
end

@everywhere begin
    using Statistics
    using Serialization
end

# Re-include on workers
@everywhere include("gen_crp_softmax.jl")
@everywhere include("find_best_alpha.jl")

@everywhere begin
    # tie-safe mode helper on workers
    function int_mode(x::Vector{Int})
        counts = Dict{Int, Int}()
        for v in x
            counts[v] = get(counts, v, 0) + 1
        end
        maxc = maximum(values(counts))
        modes = sort([k for (k, c) in counts if c == maxc])
        return modes[1]
    end

    function summarize_alpha(alpha::Float64; n_sims::Int)
        sims = explore_parameter_space(alpha; n_samples=n_sims)
        max_clus_vec = [s.max_clus for s in sims]
        planet_mode  = int_mode(max_clus_vec)
        planet_mean  = mean(max_clus_vec)
        planet_var   = var(max_clus_vec)

        hist = Dict{Int,Int}()
        for k in max_clus_vec
            hist[k] = get(hist, k, 0) + 1
        end


        return (alpha=alpha,
                planet_mode=planet_mode,
                planet_mean=planet_mean,
                planet_var=planet_var,
                planet_hist=hist)
    end
end

# -------------------------------------------------------------------
# Run sweep
# -------------------------------------------------------------------
println("Running α → planet-bin sweep on $(nprocs()) processes...")
println("ALPHAS = $(first(ALPHAS)) : $(step(ALPHAS)) : $(last(ALPHAS)) | N_SIMS = $N_SIMS")

alpha_summaries = pmap(a -> summarize_alpha(a; n_sims=N_SIMS), collect(ALPHAS))

# Sort by alpha (pmap can reorder)
alpha_summaries = sort(alpha_summaries, by = x -> x.alpha)

# -------------------------------------------------------------------
# Build "planet bins": group alphas by modal planet count
# -------------------------------------------------------------------
# This gives you equivalence classes in alpha-space.
bins = Dict{Int, Vector{Float64}}()
for s in alpha_summaries
    bins[s.planet_mode] = get(bins, s.planet_mode, Float64[])
    push!(bins[s.planet_mode], s.alpha)
end

# Also build a compact lookup table:
# alpha -> planet_mode
alpha_to_bin = [(s.alpha, s.planet_mode) for s in alpha_summaries]

# -------------------------------------------------------------------
# Save outputs
# -------------------------------------------------------------------
serialize(joinpath(OUTDIR, "alpha_summaries.ser"), alpha_summaries)
serialize(joinpath(OUTDIR, "alpha_bins_by_mode.ser"), bins)
serialize(joinpath(OUTDIR, "alpha_to_planetbin.ser"), alpha_to_bin)

# Human-readable printout
open(joinpath(OUTDIR, "alpha_planet_bins.txt"), "w") do io
    println(io, "α-grid: $(first(ALPHAS)) : $(step(ALPHAS)) : $(last(ALPHAS))")
    println(io, "N_SIMS per α: $N_SIMS\n")
    println(io, rpad("alpha",10), rpad("modeK",8), rpad("meanK",10), rpad("varK",10))
    println(io, "-"^50)
    for s in alpha_summaries
        @printf(io, "%-10.2f %-8d %-10.3f %-10.3f\n",
                s.alpha, s.planet_mode, s.planet_mean, s.planet_var)
    end
    println(io, "\nBins (grouped by modal # planets):")
    for k in sort(collect(keys(bins)))
        alist = bins[k]
        println(io, "modeK=$k: α ∈ [$(minimum(alist)), $(maximum(alist))], n=$(length(alist))")
    end
end

println("\nSaved:")
println("  - $(joinpath(OUTDIR, "alpha_summaries.ser"))")
println("  - $(joinpath(OUTDIR, "alpha_bins_by_mode.ser"))")
println("  - $(joinpath(OUTDIR, "alpha_to_planetbin.ser"))")
println("  - $(joinpath(OUTDIR, "alpha_planet_bins.txt"))")

# Quick console summary
println("\n================ α → modal planet count (bin) ================")
println(rpad("α",8), rpad("modeK",8), rpad("meanK",10), rpad("varK",10))
println("--------------------------------------------------------------")
for s in alpha_summaries
    @printf("%-8.2f %-8d %-10.3f %-10.3f\n", s.alpha, s.planet_mode, s.planet_mean, s.planet_var)
end
println("==============================================================\n")
