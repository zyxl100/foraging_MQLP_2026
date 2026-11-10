# Replication CRP + adaptive discount model fitting

## Files

Put the following files inside the **replication sample** directory, preserving `model/`:

- `run_replication_fits.py` — Windows/Python parallel launcher; validates data, extracts recorded choices, fits subjects, joins parameters to questionnaires.
- `model/replication_choice_fit.jl` — Julia trial-level likelihood + bounded Sobol search and local refinement.
- `model/particle_filter.jl` — original CRP particle-filter building blocks from `model.zip` (unchanged).

The original `model_with_beta_and_epsilon.jl`, `fit_by_planet.jl`, and `sobol_min.jl` are **not overwritten**. The revised Julia fitter implements their CRP-predictive-value, uncertainty-based discounting and softmax/lapse decision equations directly, but estimates the parameters from the observed choices instead of simulated PRT SSE. This matters for beta and epsilon.

## Setup (once)

In an ordinary Windows terminal:

```powershell
python -m pip install numpy pandas
julia -e 'using Pkg; Pkg.add(["CSV", "DataFrames", "Distributions", "StatsBase", "Sobol"])'
```

Install Julia and ensure `julia` is on PATH. If not, set `JULIA = r"C:\path\to\julia.exe"` near the top of `run_replication_fits.py`.

## Run

```powershell
python "C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\replication sample\run_replication_fits.py"
```

Or, in Jupyter notebook:

```python
%run "C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\foraging_MQLP-main\foraging_MQLP-main\replication sample\run_replication_fits.py"
```

Configure `WORKERS`, `N_SOBOL`, `N_PARTICLES`, `N_SAMPLES`, `SEED`, `REFIT`, and input filenames at top of launcher. Defaults: four Julia processes, 200 Sobol candidates plus coordinate refinement, 25 CRP particles, 200 predictive samples per decision, random seed 42.

## Inputs

- `processed data/new_pilot_data.csv` (required): numeric `sub_num`, `block`, `true_planet`, `stay_num`, `reward`; optionally `galaxy` and `fileID`.
- `processed data/new_pilot_avg.csv` (optional quality control): `sub_num`, `true_planet`, `prt`. Each planet PRT must equal its number of reward rows.
- `raw data/S_<fileID>.csv` (needed for exact subject mapping if processed data have no `fileID`). The parser extracts harvested rewards and valid keyboard choices from the raw event logs. It **requires an exact full-sequence reward match** to link `sub_num` to `fileID` and does not guess based on row order. If a raw subject file is unavailable, stays are inferred from subsequent digs, leaves from a subsequent planet in the same block, and the final decision in each block is censored.
- `processed data/replication_questionnaires.csv` (required): one row per participant, unique `fileID`.

**Note:** The two trial/planet CSVs uploaded for this task contain only 10 subjects (0–9); only one raw subject file and a one-subject questionnaire were uploaded. When you run on your PC with all raw files present, the pipeline can map the corresponding fileIDs automatically. Unmatched subjects are fitted under `sub_num` but are *not* attached to a questionnaire participant without an ID match.

## Model and fitting details

Five fitted parameters in order: `alpha`, `gamma_base`, `gamma_coef`, `beta`, `epsilon`.

Parameter ranges:

- `alpha` 0.01–10 (positive; CRP concentration)
- `gamma_base` −10–10
- `gamma_coef` −3–3 (both signs allowed)
- `beta` 0.01–5 (inverse-temperature)
- `epsilon` 0–0.10 (lapse)

At each observed harvest, the CRP particle filter infers expected next-reward decay and uncertainty from the participant's *previously observed* decays. The fitting script preserves the **source model's minus sign**:

```
gamma_effective = logistic(gamma_base - gamma_coef * uncertainty)
v_stay = expected_decay * reward
v_leave = (cumulative_reward / cumulative_elapsed_time) * (harvest_time + ITI) * gamma_effective
p_stay = (1 - epsilon) * logistic(beta * (v_stay - v_leave)) + epsilon/2
```

Uncertainty is the entropy of the `Multinomial` distribution of sampled cluster counts, as in the supplied `model_with_beta_and_epsilon.jl`, not Shannon entropy of an empirical categorical probability vector. The script computes that same multinomial entropy via a precomputed binomial-expectation formula to avoid repeating the expensive distribution-entropy calculation for every fit evaluation. Experiment time constants are copied from the model: harvest=2 s, ITI=1.5 s, travel=10 s, alien=5.5 s.

The input data's actual reward stream is *conditioned on* (not simulated), so `exp_struc.csv` and simulated unvisited planets are not needed. Observed choices with key 65 are stays and key 76 are leaves. `null` timeout decisions are ignored; if choices are not recoverable, only choices implied by the processed reward stream are used. Particle resampling uses independently deep-copied particles, and the Gaussian update's prior statistics are computed before adding the new planet, avoiding source-code bookkeeping issues. This is an updated **trial-level likelihood fit**, not numerically identical to the earlier planet-SSE optimizer.

The objective is negative Bernoulli log-likelihood across modeled decisions. Sobol candidate evaluations use common random numbers via a fixed seed, followed by bounded coordinate refinement. Since particle approximations and the inverse-temperature/lapse tradeoff can still affect identifiability, use parameter recovery before interpreting those parameters substantively.

## Outputs

Generated in `processed data`:

- `replication_model_trials.csv`: same trial rows as input plus `observed_choice` and `choice_source`; created for fitting. Original data are unchanged.
- **`replication_questionnaires.csv` updated in place** with one row per `fileID` and fitted columns `sub_num, alpha, gamma_base, gamma_coef, beta, epsilon, neg_llh, n_choices, n_rewards, n_planets, n_evaluations, n_particles, n_samples, fit_seed, fit_status`. An automatic timestamped backup is written before overwriting. If no secure ID matches exist, the original questionnaire CSV is left unchanged.

Generated in `fit_params/replication_with_beta_epsilon`:

- `sub_<sub_num>.csv`: one row of fitted estimates and fit metadata per subject.
- `sub_<sub_num>.meta.json`: cache validation hash of model code, data, and settings.
- `all_fitted_parameters.csv`: all valid fits, including unmatched numeric subjects.
- `subject_id_crosswalk.csv`: link quality and unmatched numeric subjects.
- `fitting_status.csv`: success/failure per subject (with error message).
- `questionnaires_with_fitted_parameters.csv`: same completed merge as updated questionnaire file (even if zero matches).

## Validation performed on the uploaded files

- Trial data: 2,547 harvest rows across 10 `sub_num` IDs.
- Planet summary: all 601 PRTs exactly equal trial-row counts per planet.
- Raw participant `S_5ba641d1168e5e0001e4275d.csv`: all 216 rewards match processed `sub_num=0` in order, within numeric precision.
- All 216 key 65/76 decisions for that raw participant map uniquely to the corresponding 216 processed harvests via `(planet-1, prt)` → `(planet, stay_num)`.
- Python input validation, crosswalk, choice enrichment, and merge/backup were exercised with test-only fake parameter values. **No actual Julia numerical fitting was executed in the test environment because Julia is not installed there.**
