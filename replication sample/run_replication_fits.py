"""Parallel CRP + softmax/lapse fits and safe subject-level questionnaire merge.

Run on Windows: python run_replication_fits.py

Expected layout:
replication sample/
    run_replication_fits.py
    model/particle_filter.jl
    model/replication_choice_fit.jl
    raw data/batch/S_*.csv
    processed data/new_pilot_data.csv
    processed data/new_pilot_avg.csv                 # optional, used for QC
    processed data/replication_questionnaires.csv

Requires pandas, numpy; Julia + packages CSV, DataFrames, Distributions,
StatsBase, Sobol. Never joins numeric sub_num to fileID by row order.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# =============== USER SETTINGS ===============
BASE = Path(
    r"C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview"
    r"\foraging_MQLP-main\foraging_MQLP-main\replication sample"
)
TRIAL_CSV = BASE / "processed data" / "batch3"/ "new_pilot_data_batch3.csv"
AVG_CSV = BASE / "processed data" / "batch3"/ "new_pilot_avg_batch3.csv"
QUESTIONNAIRE_CSV = BASE / "processed data" / "batch3" / "replication_questionnaires.csv"
RAW_DIR = BASE / "raw data"/ "batch3"
MODEL_SCRIPT = BASE / "model" / "replication_choice_fit.jl"
MODEL_TRIAL_CSV = BASE / "processed data" / "replication_model_trials.csv"
OUT_DIR = BASE / "fit_params" / "replication_with_beta_epsilon"
JULIA = "julia"               # or full path to julia.exe
WORKERS = min(5, os.cpu_count() or 2)
N_SOBOL = 2048
N_PARTICLES = 200
N_SAMPLES = 1000
SEED = 12
REFIT = False                 # True forces refit, e.g., after model changes
# ============================================

PARAM_COLUMNS = ["alpha", "gamma_base", "gamma_coef", "beta", "epsilon", "neg_llh"]
EXTRA_COLUMNS = ["n_choices", "n_rewards", "n_planets", "n_evaluations", "n_particles", "n_samples", "fit_seed"]
FIT_COLUMNS = PARAM_COLUMNS + EXTRA_COLUMNS
RUN_SIGNATURE = None


def compute_run_signature() -> str:
    """Invalidate caches when data, model code, or fitting settings change."""
    h = hashlib.sha256()
    for path in (MODEL_TRIAL_CSV, MODEL_SCRIPT, BASE / "model" / "particle_filter.jl"):
        h.update(path.name.encode("utf-8"))
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    h.update(json.dumps(dict(N_SOBOL=N_SOBOL, N_PARTICLES=N_PARTICLES,
                             N_SAMPLES=N_SAMPLES, SEED=SEED), sort_keys=True).encode())
    return h.hexdigest()


def validate_data(trial_csv: Path, avg_csv: Path) -> pd.DataFrame:
    d = pd.read_csv(trial_csv, low_memory=False)
    required = {"sub_num", "block", "true_planet", "stay_num", "reward"}
    if not required.issubset(d.columns):
        raise ValueError(f"Missing trial columns: {sorted(required - set(d.columns))}")
    if d[list(required)].isna().any().any():
        raise ValueError("Trial data contain missing required values")
    if d.duplicated(["sub_num", "block", "true_planet", "stay_num"]).any():
        raise ValueError("Duplicate subject/planet/stay entries")
    for (sub, block, planet), g in d.groupby(["sub_num", "block", "true_planet"], sort=False):
        vals = sorted(int(x) for x in g.stay_num)
        if vals != list(range(len(vals))):
            raise ValueError(f"Noncontiguous stay_num: subject={sub}, block={block}, planet={planet}")
    if "galaxy" in d.columns and (d.groupby(["sub_num", "block", "true_planet"]).galaxy.nunique() > 1).any():
        raise ValueError("Galaxy changes within a planet")
    if avg_csv.exists():
        a = pd.read_csv(avg_csv, low_memory=False)
        if {"sub_num", "true_planet", "prt"}.issubset(a.columns):
            actual = d.groupby(["sub_num", "true_planet"]).size().rename("n_digs").reset_index()
            merged = actual.merge(
                a[["sub_num", "true_planet", "prt"]],
                on=["sub_num", "true_planet"], how="outer", validate="one_to_one", indicator=True
            )
            if (merged["_merge"] != "both").any() or not np.allclose(merged.n_digs, merged.prt):
                raise ValueError("Planet summary PRT does not match trial data; check input versions")
            print(f"PRT QC: {len(merged)} planet records exactly match the trial data")
    return d


def reward_sequence_from_raw(path: Path) -> np.ndarray:
    """The raw harvest event's reward_received is column 14.
    Survey rows can contain unquoted commas, so do not use pd.read_csv on raw files.
    """
    rewards = []
    with path.open(encoding="utf-8-sig", errors="replace") as f:
        hdr = next(csv.reader([next(f)]))
        try:
            reward_index = hdr.index("reward_received")
        except ValueError:
            return np.array([], dtype=float)
        for line in f:
            if not line.startswith("harvest,"):
                continue
            fields = next(csv.reader([line]))
            if len(fields) > reward_index:
                try:
                    rewards.append(float(fields[reward_index]))
                except (TypeError, ValueError):
                    pass
    return np.asarray(rewards, dtype=float)


def crosswalk_from_rewards(data: pd.DataFrame) -> pd.DataFrame:
    """Safely identify fileID from exact full-sequence reward matches.
    Unmatched/ambiguous subjects remain unmapped; never guess based on order.
    """
    if "fileID" in data.columns:
        pairs = data[["sub_num", "fileID"]].drop_duplicates().copy()
        if pairs.sub_num.duplicated().any() or pairs.fileID.astype(str).duplicated().any():
            raise ValueError("Trial fileID mapping is not one-to-one")
        pairs["fileID"] = pairs.fileID.astype(str).str.strip().str.removesuffix(".csv").str.removeprefix("S_")
        pairs["match_status"] = "fileID_in_trial_data"
        return pairs

    # Capture the actual rewards in the same observed chronology as the raw events.
    original = data.sort_values(["block", "true_planet", "stay_num"], kind="stable")
    sequences = {
        int(s): g.reward.to_numpy(dtype=float)
        for s, g in original.groupby("sub_num", sort=False)
    }
    indexed = defaultdict(list)
    for sub, rewards in sequences.items():
        key = (len(rewards), tuple(np.round(rewards[: min(8, len(rewards))], 5)))
        indexed[key].append(sub)

    candidates = defaultdict(list)
    for path in sorted(RAW_DIR.glob("*.csv")):
        rewards = reward_sequence_from_raw(path)
        if not len(rewards):
            continue
        key = (len(rewards), tuple(np.round(rewards[: min(8, len(rewards))], 5)))
        for sub in indexed.get(key, []):
            if np.allclose(rewards, sequences[sub], rtol=0, atol=1e-6):
                candidates[sub].append(path.stem.removeprefix("S_"))

    rows = []
    for sub in sorted(sequences):
        matches = sorted(set(candidates.get(sub, [])))
        rows.append({
            "sub_num": sub,
            "fileID": matches[0] if len(matches) == 1 else pd.NA,
            "match_status": "exact_reward_sequence" if len(matches) == 1 else (
                "ambiguous_multiple_matches" if len(matches) > 1 else "unmatched"
            )
        })
    pairs = pd.DataFrame(rows)
    known = pairs.fileID.dropna()
    if known.duplicated().any():
        raise ValueError("Multiple processed subject numbers matched the same raw fileID")
    return pairs


def parse_raw_choices(path: Path) -> pd.DataFrame:
    """Read valid, recorded A (stay) / L (leave) decisions from raw event log.
    The experiment stores raw planet IDs as 1-based; processed planet is 0-based.
    """
    observations = []
    with path.open(encoding="utf-8-sig", errors="replace") as f:
        hdr = next(csv.reader([next(f)]))
        keys = {key: hdr.index(key) for key in ("key_press", "planet", "prt", "block_num")}
        for line in f:
            if not line.startswith("decision,"):
                continue
            cells = next(csv.reader([line]))
            if len(cells) <= max(keys.values()):
                continue
            key = cells[keys["key_press"]]
            if key not in ("65", "76"):
                continue  # timeouts / unresponded trials are not choices
            try:
                observations.append({
                    "planet": int(cells[keys["planet"]]) - 1,
                    "stay_num": int(cells[keys["prt"]]),
                    "block_check": int(cells[keys["block_num"]]),
                    "observed_choice": 1 if key == "65" else 0,
                })
            except ValueError:
                continue
    frame = pd.DataFrame(observations)
    if frame.empty:
        return pd.DataFrame(columns=["planet", "stay_num", "block_check", "observed_choice"])
    if frame.duplicated(["planet", "stay_num"]).any():
        raise ValueError(f"Duplicate recorded actions in raw file {path.name}")
    return frame


def write_model_trials(data: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Create choice-enriched trial file; no changes to original pilot data.
    Default inference: stay if more digs on same planet, leave when next planet
    is observed in same block, censor final planet at end of each block.
    Exact recorded raw decisions override default inference.
    """
    d = data.copy()
    d["observed_choice"] = np.nan
    d = d.sort_values(["sub_num", "block", "true_planet", "stay_num"], kind="stable")
    for _, g in d.groupby(["sub_num", "block", "true_planet"], sort=False):
        inds = g.index.tolist()
        d.loc[inds[:-1], "observed_choice"] = 1
    last_planets = (
        d.groupby(["sub_num", "block", "true_planet"], sort=False)["stay_num"]
         .size().reset_index()[["sub_num", "block", "true_planet"]]
    )
    last_planets["last_in_block"] = (
        last_planets.groupby(["sub_num", "block"]).true_planet
        .transform("max") == last_planets.true_planet
    )
    nonterminal = last_planets[~last_planets.last_in_block]
    for row in nonterminal.itertuples(index=False):
        idx = d.index[(d.sub_num == row.sub_num) & (d.block == row.block) &
                      (d.true_planet == row.true_planet)]
        if len(idx):
            d.loc[idx[-1], "observed_choice"] = 0
    d["choice_source"] = np.where(d.observed_choice.notna(), "inferred", "censored")

    n_raw = 0
    for row in mapping.dropna(subset=["fileID"]).itertuples(index=False):
        path = RAW_DIR / f"S_{row.fileID}.csv"
        if not path.is_file():
            continue
        decisions = parse_raw_choices(path)
        if decisions.empty:
            continue
        subset = d.loc[d.sub_num == row.sub_num, ["planet", "stay_num", "block"]].copy()
        subset["row_index"] = subset.index
        if subset.duplicated(["planet", "stay_num"]).any():
            raise ValueError(f"Processed trial planet ID not unique for subject {row.sub_num}")
        matched = subset.merge(decisions, how="inner", on=["planet", "stay_num"], validate="one_to_one")
        if len(matched):
            if (matched.block != matched.block_check).any():
                raise ValueError(f"Raw vs processed block mismatch for subject {row.sub_num}")
            d.loc[matched.row_index.to_numpy(), "observed_choice"] = matched.observed_choice.to_numpy()
            d.loc[matched.row_index.to_numpy(), "choice_source"] = "raw_decision"
            n_raw += len(matched)
        if len(decisions) != len(matched):
            raise ValueError(f"Some valid raw decisions did not match processed rewards for subject {row.sub_num}")
    d.to_csv(MODEL_TRIAL_CSV, index=False)
    print(f"Model decisions: {d.observed_choice.notna().sum()} known, "
          f"{d.observed_choice.isna().sum()} censored; {n_raw} from raw decision keys")
    return d


def run_subject(sub_num: int) -> dict:
    output = OUT_DIR / f"sub_{sub_num}.csv"
    sidecar = OUT_DIR / f"sub_{sub_num}.meta.json"
    if output.exists() and sidecar.exists() and not REFIT:
        try:
            if json.loads(sidecar.read_text(encoding="utf-8")).get("run_signature") == RUN_SIGNATURE:
                return {"sub_num": sub_num, "fit_status": "cached", "detail": ""}
        except (OSError, ValueError):
            pass
    cmd = [JULIA, "--startup-file=no", str(MODEL_SCRIPT), str(sub_num),
           str(MODEL_TRIAL_CSV), str(output), str(N_SOBOL), str(N_PARTICLES),
           str(N_SAMPLES), str(SEED)]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:
        return {"sub_num": sub_num, "fit_status": "error", "detail": str(exc)}
    if completed.returncode != 0 or not output.exists():
        detail = (completed.stderr + "\n" + completed.stdout)[-3000:].strip()
        return {"sub_num": sub_num, "fit_status": "error", "detail": detail}
    # Sidecar is created only after a successful Julia exit.
    sidecar.write_text(json.dumps({"run_signature": RUN_SIGNATURE, "sub_num": sub_num}), encoding="utf-8")
    return {"sub_num": sub_num, "fit_status": "fitted", "detail": ""}


def main():
    for p in [TRIAL_CSV, QUESTIONNAIRE_CSV, MODEL_SCRIPT, BASE / "model" / "particle_filter.jl"]:
        if not p.is_file():
            raise FileNotFoundError(f"Required input missing: {p}")
    if shutil.which(JULIA) is None and not Path(JULIA).is_file():
        raise FileNotFoundError(
            "Julia executable not found. Install Julia and/or set JULIA to the full julia.exe path."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = validate_data(TRIAL_CSV, AVG_CSV)
    subs = sorted(int(s) for s in data.sub_num.unique())
    print(f"Subjects to fit: {len(subs)}; workers: {WORKERS}; Sobol: {N_SOBOL}")
    mapping = crosswalk_from_rewards(data)
    mapping.to_csv(OUT_DIR / "subject_id_crosswalk.csv", index=False)
    print("FileID mapping status:\n", mapping.match_status.value_counts().to_string())
    write_model_trials(data, mapping)
    global RUN_SIGNATURE
    RUN_SIGNATURE = compute_run_signature()

    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {executor.submit(run_subject, s): s for s in subs}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(f"[{len(results)}/{len(subs)}] sub {result['sub_num']}: {result['fit_status']}")

    status = pd.DataFrame(results)
    status.to_csv(OUT_DIR / "fitting_status.csv", index=False)
    fits = []
    valid_subs = set(status.loc[status.fit_status.isin(["fitted", "cached"]), "sub_num"])
    for s in sorted(valid_subs):
        p = OUT_DIR / f"sub_{s}.csv"
        if not p.exists():
            continue
        try:
            rec = pd.read_csv(p)
            if len(rec) == 1 and int(rec.loc[0, "sub_num"]) == s and rec[PARAM_COLUMNS].notna().all(axis=None):
                fits.append(rec)
        except (OSError, ValueError, KeyError):
            pass
    if not fits:
        print("No valid fit files: questionnaire CSV was not modified.")
        return
    all_fits = pd.concat(fits, ignore_index=True)
    if all_fits.sub_num.duplicated().any():
        raise ValueError("Duplicate fitted sub_num")
    joined = all_fits.merge(mapping, on="sub_num", how="left", validate="one_to_one")
    joined = joined.merge(status[["sub_num", "fit_status"]], on="sub_num", how="left", validate="one_to_one")
    joined.to_csv(OUT_DIR / "all_fitted_parameters.csv", index=False)

    questionnaire = pd.read_csv(QUESTIONNAIRE_CSV, dtype={"fileID": "string"})
    if "fileID" not in questionnaire:
        raise ValueError("Questionnaire CSV must include fileID")
    questionnaire["fileID"] = questionnaire.fileID.str.strip().str.removesuffix(".csv").str.removeprefix("S_")
    if questionnaire.fileID.isna().any() or questionnaire.fileID.duplicated().any():
        raise ValueError("Questionnaire fileID must be nonmissing and unique")

    # Existing columns from an earlier fit are replaced, not duplicated as _x/_y.
    previous = ["sub_num"] + FIT_COLUMNS + ["fit_status"]
    questionnaire = questionnaire.drop(columns=[c for c in previous if c in questionnaire.columns])
    fits_for_merge = joined.dropna(subset=["fileID"])[["fileID", "sub_num"] + FIT_COLUMNS + ["fit_status"]]
    fits_for_merge["fileID"] = fits_for_merge.fileID.astype("string")
    if fits_for_merge.fileID.duplicated().any():
        raise ValueError("More than one fit for a questionnaire fileID")
    combined = questionnaire.merge(fits_for_merge, on="fileID", how="left", validate="one_to_one", indicator=True)
    matches = int((combined["_merge"] == "both").sum())
    combined.drop(columns=["_merge"], inplace=True)
    if len(combined) != len(questionnaire):
        raise AssertionError("Subject-level merge changed questionnaire row count")
    combined.to_csv(OUT_DIR / "questionnaires_with_fitted_parameters.csv", index=False, encoding="utf-8-sig")

    missing_fit = joined[joined.fileID.isna()]
    missing_q = joined[joined.fileID.notna() & ~joined.fileID.astype(str).isin(questionnaire.fileID.astype(str))]
    print(f"Fitted subjects: {len(all_fits)}/{len(subs)}; questionnaire rows matched: {matches}/{len(questionnaire)}")
    print(f"Fitted subjects lacking fileID crosswalk: {len(missing_fit)}; IDs absent from questionnaire: {len(missing_q)}")
    if not matches:
        print("No safe subject match, so original questionnaire file was NOT overwritten.")
        return
    backup = QUESTIONNAIRE_CSV.with_name(
        QUESTIONNAIRE_CSV.stem + ".before_model_fit_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
    )
    shutil.copy2(QUESTIONNAIRE_CSV, backup)
    temp = QUESTIONNAIRE_CSV.with_name(QUESTIONNAIRE_CSV.name + ".tmp")
    combined.to_csv(temp, index=False, encoding="utf-8-sig")
    os.replace(temp, QUESTIONNAIRE_CSV)
    print(f"Updated: {QUESTIONNAIRE_CSV}")
    print(f"Original backed up: {backup}")
    print(f"All fitting outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
