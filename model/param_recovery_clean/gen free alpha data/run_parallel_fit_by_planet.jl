# =====================================================================
# run_parallel_fit_by_planet.jl
# Fully robust parallel launcher:
#  - auto-detect subject list
#  - skip already-fitted subjects
#  - skip subjects that error out
#  - clean logging only
# =====================================================================

using Distributed
using CSV
using DataFrames
using JLD

# -------------------------------------------------------
# 1. Add worker processes
# -------------------------------------------------------
n_workers = 10
addprocs(n_workers)

@info "Launched $(nworkers()) workers."

# -------------------------------------------------------
# 2. Load compute code on all workers
# -------------------------------------------------------
@everywhere include("fit_by_planet.jl")

# -------------------------------------------------------
# 3. Extract subject numbers from CSV
# -------------------------------------------------------
df = CSV.read("data/simulated_structure_learning_RANDOM_300.csv", DataFrame)
all_subjects = sort(unique(df.sub_num))

model_num = 0  # structural learning model

# -------------------------------------------------------
# 4. Identify subjects that already have .jld files
# -------------------------------------------------------
function already_fitted(sub)
    fname = "fit_params/adaptive_discount_all_sim/sub$(sub).jld"
    return isfile(fname)
end

subjects_to_run = [s for s in all_subjects if !already_fitted(s)]

@info "Detected subjects in dataset: $all_subjects"
@info "Already fitted subjects skipped: $([s for s in all_subjects if already_fitted(s)])"
@info "Subjects to run now: $subjects_to_run"

# -------------------------------------------------------
# 5. Robust subject runner
# -------------------------------------------------------
@everywhere function run_one_subject_safe(sub, model_num)
    println("\n--- Starting subject $sub ---")

    try
        # Run fit_by_planet quietly
        run(pipeline(`julia fit_by_planet.jl $sub $model_num`,
                     stdout=devnull, stderr=devnull))

        println("--- Finished subject $sub ---")
        return (sub, :ok)

    catch err
        println("--- ERROR fitting subject $sub: $err ---")
        return (sub, :error)
    end
end

# -------------------------------------------------------
# 6. Parallel execution with pmap
# -------------------------------------------------------
results = pmap(sub -> run_one_subject_safe(sub, model_num), subjects_to_run)

@info "Parallel fitting finished."

# -------------------------------------------------------
# 7. Summary report
# -------------------------------------------------------
successful = [r[1] for r in results if r[2] == :ok]
failed     = [r[1] for r in results if r[2] == :error]

println("\n===== SUMMARY =====")
println("Successful fits: $successful")
println("Failed fits:     $failed")
println("===================\n")



