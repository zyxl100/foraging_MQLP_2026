# print_jld_files.jl
# Print contents of all sub*.jld files in a folder

using JLD
using Printf

# Folder containing your JLD files
dir = raw"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\model\fit_params\adaptive_discount_online_08_21_24"

# Find JLD files like sub1.jld, sub2.jld, ...
files = filter(f -> endswith(f, ".jld") && occursin(r"^sub\d+\.jld$", f),
               readdir(dir))

if isempty(files)
    println("❌ No sub*.jld files found.")
else
    for f in sort(files)
        fullpath = joinpath(dir, f)

        println("\n===================================================")
        @printf("📄 FILE: %s\n", f)
        println("---------------------------------------------------")

        try
            data = JLD.load(fullpath)

            println("📦 Variables in file:")
            println(keys(data))

            println("\n🔍 Full contents:")
            for (k, v) in data
                println("---------------------------------------------------")
                @printf("[%s] =>\n", k)
                println(v)
            end

        catch e
            println("❌ ERROR reading file $f: $e")
        end
    end
end
