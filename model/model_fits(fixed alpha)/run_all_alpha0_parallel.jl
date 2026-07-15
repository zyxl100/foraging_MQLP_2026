###############################################################################
# run_all_alpha1_parallel_SOFTMAX_ONLY.jl
# Skips CRP inference and directly runs Softmax fits
# Requires: crp_latents_alpha_1/sub*.ser files already exist
###############################################################################

# using Pkg
# Pkg.activate(".")
# Pkg.instantiate()
# Pkg.add(["CSV", "DataFrames", "Printf", "Dates"])
# Pkg.precompile()

# using Sys: free_memory

using Pkg
Pkg.activate(".")
Pkg.instantiate()
Pkg.precompile()


using CSV, DataFrames, Printf, Dates

const DATA_PATH = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\data\modeling_data\all_data_online_07_02_24.csv"
const ALPHA_LEVEL = 0
const SOFTMAX_DIR = raw".\softmax"
const OUT_SUMMARY = raw".\outs\fit_all_alpha0_summary.csv"
const JULIA_EXE = "julia --color=no --startup-file=no --quiet"

function run_julia_script(script::AbstractString, args::Vector{<:AbstractString})
    parts = String[
        "julia",                # executable
        "--startup-file=no",    # no startup.jl messages
        "--quiet",              # suppress banner
        "--color=no",           # no color codes
        "--project=.",          # activate project
        script                  # the target script
    ]
    append!(parts, args)
    return Cmd(parts)
end

function run_safe(cmd::Cmd)
    try
        println("→ ", cmd)
        # redirect stdout and stderr to null to suppress PyBADS console output
        run(pipeline(cmd, stdout=devnull, stderr=devnull))
    catch e
        @warn "Command failed" cmd exception=(e, catch_backtrace())
    end
end



function read_subject_ids(path)
    df = CSV.read(path, DataFrame; normalizenames=true)
    cols = Symbol.(lowercase.(string.(names(df))))
    rename!(df, Dict(names(df) .=> cols))
    sub_col = findfirst(x -> occursin("fileid", String(x)) || occursin("sub", String(x)), names(df))
    unique(skipmissing(df[:, sub_col]))
end



# function run_softmax_all(subjects)
#     println("\n=== Softmax fitting using existing CRP latents ===")
#     for (i, s) in enumerate(subjects)
#         @printf("[%d/%d] Subject %s\n", i, length(subjects), s)
#         cmd = run_julia_script("run_softmax_alpha_free_modif.jl",
#                                [string(ALPHA_LEVEL), string(s), SOFTMAX_DIR])
#         run_safe(cmd)
#         println("✅ Finished subject $(s)")   # <— new line, prints from parent process
#     end
# end

function run_softmax_all(subjects)
    println("\n=== Softmax fitting using existing CRP latents ===")

    # Choose how many subjects to run at once (max 10)
    batch_size = 20
    n_subs = length(subjects)

    for batch_start in 1:batch_size:n_subs
        batch_end = min(batch_start + batch_size - 1, n_subs)
        batch = subjects[batch_start:batch_end]

        println("\n→ Launching batch $(batch_start):$(batch_end) ($(length(batch)) subjects)")

        tasks = [
            Threads.@spawn begin
                s = batch[i]
                @printf("[Thread %d] Subject %s\n", Threads.threadid(), s)
                cmd = run_julia_script("run_softmax_alpha_free_modif.jl",
                                       [string(ALPHA_LEVEL), string(s), SOFTMAX_DIR])
                run_safe(cmd)
                println("✅ Finished subject $(s)")
            end for i in eachindex(batch)
        ]

        # Wait for all threads in this batch to finish before starting next 10
        for t in tasks
            fetch(t)
        end
    end
end


function collect_softmax_results(subjects::Vector)
    softmax_dir = joinpath(@__DIR__, "softmax", "neg_llh_alpha_0")
    all_files = readdir(softmax_dir; join=true)
    files = filter(f -> occursin(r"softmax_alpha\d+_", f) && endswith(f, ".csv"), all_files)

    dfs = DataFrame[]
    for f in files
        df = CSV.read(f, DataFrame)
        push!(dfs, df[1:1, :])
    end

    combined = vcat(dfs...; cols=:union)
    CSV.write(OUT_SUMMARY, combined)
    println("✅ Saved summary → $OUT_SUMMARY")
end

function main()
    println("Running SOFTMAX-ONLY pipeline @ $(Dates.format(now(), "HH:MM:SS"))")
    #subjects = read_subject_ids(DATA_PATH)          # ← runs on ALL subjects
    subjects = read_subject_ids(DATA_PATH)[1:8]   # ← for testing
    run_softmax_all(subjects)
    collect_softmax_results([subjects])
    println("\n🎉 All softmax fits completed.")
end

main()

