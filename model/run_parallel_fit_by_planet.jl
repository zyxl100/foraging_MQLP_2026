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
df = CSV.read("data/all_data_by_planet_online_final.csv", DataFrame)
all_subjects = sort(unique(df.sub_num))

model_num = 0  # structural learning model

# -------------------------------------------------------
# 4. Identify subjects that already have .jld files
# -------------------------------------------------------
function already_fitted(sub)
    fname = "fit_params/adaptive_discount_all_with_beta_and_epsilon/sub$(sub).jld"
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



#Detected subjects = [1, 2, 3, 5, 7, 10, 11, 12, 13, 14, 16, 18, 20, 21, 23, 27, 28, 29, 32, 33, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 50, 51, 53, 54, 56, 57, 58, 60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 81, 82, 83, 85, 86, 87, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 104, 105, 108, 110, 111, 112, 113, 114, 117, 118, 119, 120, 121, 122, 123, 125, 127, 129, 130, 131, 136, 137, 138, 139, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 155, 156, 158, 161, 163, 164, 167, 170, 171, 172, 173, 174, 176, 177, 178, 180, 181, 182, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 197, 198, 200, 201, 202, 203]