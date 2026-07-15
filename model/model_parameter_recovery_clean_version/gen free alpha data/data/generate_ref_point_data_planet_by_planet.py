"""
generate_ref_point_data_planet_by_planet.py

Generate planet-level reference-point data.

Works with either:
1. all_data_sim_alpha_free.csv
   columns include: sub_num, true_planet, galaxy, prt

2. simulated_structure_learning_RANDOM_300.csv
   columns include: sub_num, planet_num, galaxy, stay_num

Output:
    ref_point_data_planet_by_planet_sim.csv

Expected output columns:
    Unnamed: 0, sub_num, true_planet, galaxy, prt
"""

from pathlib import Path
import pandas as pd


# Change this if needed
INPUT_FILE = Path("simulated_structure_learning_RANDOM_300.csv")
OUTPUT_FILE = Path("ref_point_data_planet_by_planet_sim_300.csv")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find input file:\n{INPUT_FILE.resolve()}"
        )

    print(f"Reading: {INPUT_FILE.resolve()}")
    df = pd.read_csv(INPUT_FILE)

    print("\nExisting columns:")
    print(list(df.columns))

    if "sub_num" not in df.columns:
        raise ValueError("Missing required column: sub_num")

    if "galaxy" not in df.columns:
        raise ValueError("Missing required column: galaxy")

    # ------------------------------------------------------------
    # Case 1: file already has true_planet
    # ------------------------------------------------------------
    if "true_planet" in df.columns:
        planet_col = "true_planet"

    # ------------------------------------------------------------
    # Case 2: generated simulation file uses planet_num
    # ------------------------------------------------------------
    elif "planet_num" in df.columns:
        planet_col = "planet_num"
        df["true_planet"] = df["planet_num"]

    else:
        raise ValueError(
            "Could not find a planet identifier column. "
            "Expected either true_planet or planet_num."
        )

    # ------------------------------------------------------------
    # Case 1: file already has prt
    # ------------------------------------------------------------
    if "prt" in df.columns:
        prt_source = "prt"

    # ------------------------------------------------------------
    # Case 2: derive prt from stay_num
    # ------------------------------------------------------------
    elif "stay_num" in df.columns:
        prt_source = "stay_num"

    else:
        raise ValueError(
            "Could not find a PRT column. "
            "Expected either prt or stay_num."
        )

    # Make sure key columns are numeric
    for col in ["sub_num", "true_planet", "galaxy", prt_source]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["sub_num", "true_planet", "galaxy", prt_source]).copy()

    df["sub_num"] = df["sub_num"].astype(int)
    df["true_planet"] = df["true_planet"].astype(int)
    df["galaxy"] = df["galaxy"].astype(int)

    # ------------------------------------------------------------
    # Planet-level summary
    # ------------------------------------------------------------
    ref = (
        df.groupby(["sub_num", "true_planet"], as_index=False)
          .agg(
              galaxy=("galaxy", "first"),
              prt=(prt_source, "max")
          )
    )

    ref["prt"] = ref["prt"].round().astype(int)

    ref = ref.sort_values(["sub_num", "true_planet"]).reset_index(drop=True)

    # Match your reference file:
    # Unnamed: 0, sub_num, true_planet, galaxy, prt
    ref = ref[["sub_num", "true_planet", "galaxy", "prt"]]

    ref.to_csv(OUTPUT_FILE, index=True)

    print(f"\nSaved: {OUTPUT_FILE.resolve()}")
    print(f"Output shape: {ref.shape}")

    print("\nPreview:")
    print(ref.head(10).to_string(index=True))

    print("\nSubject count:", ref["sub_num"].nunique())
    print("Planet rows:", len(ref))

    print("\nPlanet count per first 10 subjects:")
    print(
        ref.groupby("sub_num")["true_planet"]
           .nunique()
           .head(10)
           .to_string()
    )


if __name__ == "__main__":
    main()