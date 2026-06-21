---
name: carbon-literature-bo-replay
description: Use this skill for literature-derived biomass carbon, hard carbon, SIB/LIB/aqueous-supercapacitor datasets when the user wants data-quality audit, protocol-aware ML baselines, offline Bayesian-optimization replay, paper-level leakage checks, suspicious outlier triage, or a modeling-ready dataset. Do not use it for generic BO algorithm development, clean benchmark optimization, or claims of real closed-loop material discovery without new experiments.
---

# Carbon Literature BO Replay Skill

## Purpose

Use this skill to evaluate whether a messy literature-derived carbon-electrode database can support ML or active-learning-style prioritization. The skill is designed for biomass-derived carbon, hard carbon, sodium-ion batteries, lithium-ion batteries, and aqueous supercapacitors.

This skill does **not** invent a new BO algorithm and must not present offline replay as real material discovery. Its job is to audit data quality, reduce paper-level leakage, expose protocol confounding, run conservative baselines, and generate a queue of samples that require source-PDF rechecking before interpretation.

## Required inputs

Accept one or more CSV/XLSX files. Prefer a single modeling table. If multiple tables are supplied, first identify the table/sheet containing sample-level records.

Minimum useful columns:

- identifiers: `sample_id`, `paper_id`, `year`, `doi`, `source_location`
- material descriptors: `precursor`, `carbonization_temperature_c`, `bet_m2_g`, `d002_nm`, `id_ig`, `n_at_percent`, `o_at_percent`
- protocol descriptors: `electrolyte`, `current_density_mag`, `mass_loading_mg_cm2`, `voltage_window`
- targets: `ice_percent`, `reversible_capacity_mah_g`, or a user-specified target
- quality flags: `quality_tier`, `needs_manual_check`

If the user has not provided real data, use the synthetic demo only to validate the pipeline. Explicitly state that the demo is synthetic and cannot support scientific claims.

## Workflow

### 1. Intake and scope lock

1. Identify the target variable. Default priorities:
   - SIB hard carbon: `ice_percent`, then `reversible_capacity_mah_g`.
   - LIB biomass carbon: `reversible_capacity_mah_g`, then `ice_percent`.
   - Aqueous SC: `specific_capacitance_f_g`, then `capacitance_retention_percent`.
2. Identify whether the user wants:
   - data audit only;
   - ML baseline only;
   - offline BO replay;
   - full audit + replay pipeline.
3. Record whether the dataset is real, demo, synthetic, or unknown.
4. Do not fabricate missing DOI, source location, values, or quality tiers.

### 2. Dataset audit

Run or emulate `scripts/audit_dataset.py`.

Audit outputs must include:

- missingness by column;
- duplicate `sample_id` and duplicate sample signatures;
- samples per `paper_id`;
- top papers dominating the dataset;
- protocol completeness;
- quality-tier distribution;
- suspicious target outliers;
- high-performance samples needing source-PDF recheck;
- modeling-ready export with stable column names.

Flag P0 risk if any of the following occurs:

- target variable is missing or mostly empty;
- `paper_id` is missing, preventing leakage checks;
- too few non-missing target values for replay;
- source information is absent for claimed real data;
- unit ambiguity affects the selected target.

### 3. Protocol-aware filtering

Before modeling, separate raw target analysis from protocol-filtered analysis.

Recommended filters:

- SIB/LIB: keep consistent half-cell data and report current density; if current density is missing, flag but do not silently drop unless the user requests strict mode.
- Aqueous SC: distinguish two-electrode vs three-electrode data; do not mix capacitance values without device configuration and current density notes.
- Avoid comparing capacity/capacitance values measured under very different rates without a protocol confounding warning.

### 4. Splits and leakage checks

Always compare random split against at least one leakage-aware split if enough data exist:

- `random_split`: useful but optimistic.
- `leave_one_paper_out`: preferred leakage stress test.
- `time_split`: train on earlier years, evaluate on later years when year coverage permits.

Warn if random split performs well but paper-level split collapses.

### 5. Baselines

Run conservative baselines before BO replay:

- median predictor;
- random forest or extra trees regression;
- gradient boosting regression when available;
- optional Gaussian process only when feature count and sample size are appropriate.

Report RMSE/MAE/R² or ranking metrics. For small datasets, prioritize ranking utility and stability over R².

### 6. Offline BO replay

Use offline replay as a historical prioritization test:

1. Start from a small random initial set.
2. Train a surrogate model.
3. Score unobserved candidates by acquisition, typically `mean + beta * uncertainty`.
4. Reveal the selected candidate's known literature target.
5. Repeat until budget is exhausted.
6. Compare against random search over multiple seeds.

Required outputs:

- best-so-far curve;
- final best target distribution over seeds;
- top candidate queue;
- source-PDF recheck queue;
- summary of whether BO materially beats random search.

Do not call the selected candidates “new discoveries.” Use “prioritized historical candidates” or “offline replay recommendations.”

### 7. Data-quality ablation

When `quality_tier` exists, compare:

- all samples;
- Tier 0–1 only;
- suspicious samples removed;
- manually checked samples only, if available.

If performance depends strongly on Tier 2/3 or suspicious samples, conclude that the dataset is not yet robust enough for claims.

### 8. Final report standard

Every final response or generated report should include:

- dataset size and non-missing target count;
- target and protocol assumptions;
- key missingness bottlenecks;
- leakage risk;
- protocol confounding risk;
- top candidates and whether they need manual recheck;
- whether the result supports BO-style prioritization, only ML screening, or more data curation first.

Use severity labels:

- P0 = invalidates modeling or replay until fixed;
- P1 = serious risk; interpret results as exploratory;
- P2 = useful improvement; not blocking.

## Commands

Synthetic demo:

```bash
python scripts/run_pipeline.py \
  --input examples/sib_hard_carbon_synthetic/synthetic_sib_hard_carbon.csv \
  --target ice_percent \
  --outdir outputs/synthetic_demo
```

Real dataset:

```bash
python scripts/run_pipeline.py \
  --input data/raw/sib_hard_carbon_real.csv \
  --target ice_percent \
  --outdir outputs/sib_real_ice
```

Audit only:

```bash
python scripts/audit_dataset.py \
  --input data/raw/sib_hard_carbon_real.csv \
  --target ice_percent \
  --outdir outputs/sib_audit
```

Replay only on a prepared table:

```bash
python scripts/run_offline_bo_replay.py \
  --input data/modeling_ready/sib_modeling_ready.csv \
  --target ice_percent \
  --outdir outputs/sib_bo_replay
```

## Guardrails

- Do not fabricate source data.
- Do not hide missingness by filling values without a clear imputation log.
- Do not mix device systems or protocols without warnings.
- Do not interpret SHAP or feature importance causally.
- Do not claim real closed-loop discovery from offline replay.
- Always surface samples that could dominate conclusions and require manual source checking.
