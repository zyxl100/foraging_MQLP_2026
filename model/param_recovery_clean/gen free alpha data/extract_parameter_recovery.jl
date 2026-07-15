using JLD2
using DataFrames
using CSV

###############################################################
# 1. PATHS (your actual working paths)
###############################################################

base_dir = @__DIR__

#ground_truth_file = joinpath(base_dir, "data", "all_data_sim_alpha_free.csv")
ground_truth_file = joinpath(base_dir, "data", "simulated_structure_learning_RANDOM_300.csv")


# Folder where subXX.jld files live
jld_folder = joinpath(base_dir, "fit_params", "adaptive_discount_all_sim")

println("Reading JLD folder: ", jld_folder)
println("Files in folder:")
println(readdir(jld_folder))


###############################################################
# 2. List JLD files
###############################################################

# Pick only .jld files
jld_files = filter(f -> endswith(f, ".jld"), readdir(jld_folder))

println("\nFound JLD files:")
println(jld_files)


###############################################################
# 3. Load ground-truth
###############################################################

gt = DataFrame(CSV.File(ground_truth_file))

# Ground truth stored per planet → collapse to 1 row per subject
gt_unique = unique(gt[:, [
    :sub_num,
    :alpha,
    :gamma_base,
    :gamma_coef,

]])

rename!(gt_unique, Dict(
    :alpha => :alpha_true,
    :gamma_base => :gamma_base_true,
    :gamma_coef => :gamma_coef_true,

))

println("\nLoaded ground-truth for ", nrow(gt_unique), " subjects.")


###############################################################
# 4. Extract inferred parameters
###############################################################

inferred = DataFrame(
    sub_num = Int[],
    alpha_est = Float64[],
    gamma_base_est = Float64[],
    gamma_coef_est = Float64[],

)

for file in jld_files
    filepath = joinpath(jld_folder, file)
    println("Loading: ", filepath)

    # Extract "50" from "sub50.jld"
    m = match(r"sub(\d+)\.jld", file)
    sub_num = parse(Int, m.captures[1])

    d = load(filepath)

    if !haskey(d, "res")
        println("WARNING: missing key 'res' in ", file)
        continue
    end

    p = d["res"]   # NamedTuple

    push!(inferred, (
        sub_num,
        p.a,
        p.b,
        p.c,

    ))
end

println("\nExtracted inferred params for ", nrow(inferred), " subjects.")


###############################################################
# 5. Merge and save
###############################################################

merged = leftjoin(inferred, gt_unique, on = :sub_num)

out_csv = joinpath(base_dir, "parameter_recovery_results.csv")
CSV.write(out_csv, merged)

println("\n--------------------------------------------------")
println("Parameter recovery CSV saved to:")
println(out_csv)
println("--------------------------------------------------")
