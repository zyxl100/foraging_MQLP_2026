using CSV
using DataFrames
using Printf

###############################################################
# 1. PATH SETUP
###############################################################

result_df_folder = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\data\result_df"

foraging_file = joinpath(
    result_df_folder,
    "all_foraging_data_07_02_24.csv"
)

param_file = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\fit_params\adaptive_discount_all_with_beta_and_epsilon\fitted_parameters_by_subject.csv"

save_file = joinpath(
    result_df_folder,
    "all_foraging_data_07_02_24_with_gamma_positive_params.csv"
)

println("Foraging data file: ", foraging_file)
println("Parameter file:     ", param_file)
println("Output file:        ", save_file)


###############################################################
# 2. LOAD DATA
###############################################################

foraging_df = DataFrame(CSV.File(foraging_file))
param_df    = DataFrame(CSV.File(param_file))

println("Loaded foraging_df: ", nrow(foraging_df), " rows")
println("Loaded param_df:    ", nrow(param_df), " rows")


###############################################################
# 3. RENAME PARAMETER COLUMNS (EXCEPT sub_num)
###############################################################

join_key = :sub_num

rename_map = Dict{Symbol,Symbol}()

for col in names(param_df)
    col_sym = Symbol(col)   # <-- critical fix

    if col_sym != join_key
        rename_map[col_sym] = Symbol(col_sym, "_gamma_positive")
    end
end

rename!(param_df, rename_map)

println("Renamed parameter columns:")
for (k, v) in rename_map
    println("  ", k, " → ", v)
end


###############################################################
# 4. JOIN ON sub_num
###############################################################

@assert join_key in Symbol.(names(foraging_df))
@assert join_key in Symbol.(names(param_df))

final_df = leftjoin(
    foraging_df,
    param_df,
    on = join_key
)

println("After join: ", nrow(final_df), " rows")


###############################################################
# 5. SAVE
###############################################################

CSV.write(save_file, final_df)

println("\n--------------------------------------------------")
println("Merged file saved successfully")
println("Rows: ", nrow(final_df))
println("File: ", save_file)
println("--------------------------------------------------")
