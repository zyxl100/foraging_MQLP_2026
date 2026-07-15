using JLD2
using CSV
using DataFrames
using Printf

###############################################################
# 1. PATH SETUP
###############################################################

fit_folder = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\fit_params\adaptive_discount_all_with_beta_and_epsilon"

save_file = joinpath(fit_folder, "fitted_parameters_by_subject.csv")

println("Fit folder: ", fit_folder)
println("Output CSV: ", save_file)


###############################################################
# 2. FIND JLD / JLD2 FILES
###############################################################

files = filter(f -> endswith(f, ".jld") || endswith(f, ".jld2"), readdir(fit_folder))
println("Found ", length(files), " JLD files.")


###############################################################
# 3. EXTRACT PARAMETERS
###############################################################

param_df = DataFrame(
    sub_num          = Int[],
    alpha_free       = Float64[],
    gamma_base_free  = Float64[],
    gamma_coef_free  = Float64[],
    beta_free        = Float64[],
    epsilon_free     = Float64[]
)

for f in files
    fpath = joinpath(fit_folder, f)

    # Expect filenames like sub23.jld or sub23.jld2
    m = match(r"sub(\d+)\.jld2?", f)
    if m === nothing
        @printf("Skipping file (cannot parse subject id): %s\n", f)
        continue
    end

    subn = parse(Int, m.captures[1])

    d = load(fpath)

    if !haskey(d, "res")
        @printf("Skipping file (missing 'res'): %s\n", f)
        continue
    end

    p = d["res"]  # NamedTuple (a, b, c, d, e)

    push!(param_df, (
        subn,
        float(p.a),
        float(p.b),
        float(p.c),
        float(p.d),
        float(p.e)
    ))
end


###############################################################
# 4. SORT & SAVE
###############################################################

sort!(param_df, :sub_num)

CSV.write(save_file, param_df)

println("\n--------------------------------------------------")
println("Saved fitted parameters CSV")
println("Rows: ", nrow(param_df))
println("File: ", save_file)
println("--------------------------------------------------")
