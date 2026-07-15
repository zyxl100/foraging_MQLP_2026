
using Distributed, Serialization, Statistics, Printf




const OUTDIR = "results"
const TRUE_K = 3
const ALPHAS = 0.0:0.05:1
const N_SIMS = parse(Int, get(ENV, "N_SIMS", "100"))
mkpath(OUTDIR)


addprocs(parse(Int, get(ENV, "SLURM_CPUS_PER_TASK", "8")))
@everywhere begin
    using Statistics, Serialization
    include("gen_crp_softmax.jl")
    include("find_best_alpha.jl")
    const N_SIMS = parse(Int, get(ENV, "N_SIMS", "100"))
    const TRUE_K = 3



    function run_alpha(α)
        

        sims = explore_parameter_space(α; n_samples=N_SIMS)
        max_clus_vec = [s.max_clus for s in sims]
        reward_vec   = [s.total_reward for s in sims]

        veridical_hits = count(x -> x == TRUE_K, max_clus_vec)
        veridical_prop = veridical_hits / N_SIMS
        mean_reward = mean(reward_vec)

        serialize(joinpath("results", "alpha_$(α)_sims.ser"), sims)

        return (alpha=α, veridical_prop=veridical_prop,
                mean_reward=mean_reward, reward_vec=reward_vec,
                veridical_hits=veridical_hits)
    end

end

println("Running distributed α search on $(nprocs()) processes...")
alpha_summary = pmap(run_alpha, collect(ALPHAS))

# --- SAVE SUMMARY ---
serialize(joinpath(OUTDIR, "alpha_grid_summary.ser"), alpha_summary)

# --- DISPLAY RESULTS ---
println("\n=================== α Performance Summary ===================")
println(rpad("α",6), rpad("Veridical%",14), rpad("Hits",8), rpad("MeanReward",14))
println("-------------------------------------------------------------")
for as in alpha_summary
    @printf("%-6.2f %-14.2f %-8d %-14.2f\n",
        as.alpha, 100*as.veridical_prop, as.veridical_hits, as.mean_reward)
end

# --- SELECT BEST α ---
best = argmax([(as.veridical_prop, as.veridical_hits, as.mean_reward) for as in alpha_summary])
alpha_star = alpha_summary[best].alpha
println("-------------------------------------------------------------")
println("Best α* = ", alpha_star)
println("=============================================================\n")


