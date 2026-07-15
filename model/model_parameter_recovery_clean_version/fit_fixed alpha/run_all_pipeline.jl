# run_all_pipeline.jl
# One-shot batch pipeline: CRP latents (α=0,1) + regular fits + moving-window fits for all subjects.

using CSV, DataFrames
using Printf

# ---------- CONFIG ----------
const AGES_CSV   = joinpath("data", "sub_ages_20240417.csv")
const OUT_DIR    = "outs"                  # where mw CSVs go
const SOFTMAX_DIR= "softmax"               # where regular fit CSVs go (kept by the called script)
const WINDOW_LEN = 60
const STEP_SIZE  = 20
const ALPHAS     = [0, 1]                  # 0→α=0.0, 1→α=0.2
const JULIA_EXE  = "julia"                 # assumes julia is on PATH
# --------------------------------

# normalize column names, robust to BOM/weird chars
function read_subject_ids(path::AbstractString)
    ages = CSV.read(path, DataFrame; normalizenames=true)
    # lowercase symbolic names, strip leading non-alnum, collapse the rest to underscores
    old = names(ages)
    norm = Symbol.(replace.(lowercase.(string.(old)),
                            r"^\W+" => "", r"[^a-z0-9]+" => "_"))
    rename!(ages, Dict(old .=> norm))
    # candidates for subject id column
    sub_candidates = [:sub_num, :subject_num, :subject, :sub, :id]
    sub_matches = [c for c in sub_candidates if c in names(ages)]
    sub_sym = isempty(sub_matches) ? names(ages)[1] : sub_matches[1]  # fallback: first column
    unique(skipmissing(ages[!, sub_sym]))
end

# run a command and echo it nicely
function rung(cmd::Cmd)
    println("→ ", cmd)
    run(cmd)
end

# helper to build a julia command that runs a script with arguments in THIS project
function jcmd(script::AbstractString, args::AbstractVector{<:AbstractString})
    parts = String[JULIA_EXE, "--project=.", script]
    append!(parts, args)
    return Cmd(parts)  # pass args as separate tokens (no accidental concatenation)
end


# ---------- MAIN ----------
function main()
    # sanity: ensure OUT_DIR exists
    isdir(OUT_DIR) || mkpath(OUT_DIR)

    # discover subjects
    subjects = collect(read_subject_ids(AGES_CSV))
    @printf("Found %d subjects from %s\n", length(subjects), AGES_CSV)

    # 1) Generate CRP latents for each alpha and subject
    for a in ALPHAS
        println("\n=== Generating CRP latents (alpha_level = $a) ===")
        for s in subjects
            rung(jcmd("run_crp_alpha_free_modif.jl", [string(a), string(s)]))
        end
    end

    # 2) Regular (full-sequence) softmax fits for each alpha and subject
    for a in ALPHAS
        println("\n=== Regular softmax fits (alpha_level = $a) ===")
        for s in subjects
            rung(jcmd("run_softmax_alpha_free_modif.jl", [string(a), string(s), SOFTMAX_DIR]))
        end
    end

    # 3) Moving-window fits for ALL subjects at once (one CSV per alpha)
    for a in ALPHAS
        println("\n=== Moving-window fits (alpha_level = $a, window=$WINDOW_LEN, step=$STEP_SIZE) ===")
        out_csv = joinpath(OUT_DIR, @sprintf("mw_alpha%d_all.csv", a))
        rung(jcmd("run_fit_moving_window.jl",
                  [string(a), string(WINDOW_LEN), string(STEP_SIZE), AGES_CSV, out_csv]))
    end

    println("\nAll done.")
    println("Regular fit outputs:  $(joinpath(SOFTMAX_DIR, "neg_llh_alpha_<a>\\sub<id>.csv"))")
    println("Moving-window outputs: $(joinpath(OUT_DIR, "mw_alpha0_all.csv")) and mw_alpha1_all.csv")
end

main()
