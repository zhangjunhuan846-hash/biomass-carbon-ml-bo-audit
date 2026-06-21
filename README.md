# carbon-literature-bo-replay-skill

A Codex-ready skill and lightweight Python workflow for **data-quality-aware offline Bayesian-optimization replay** on literature-derived biomass carbon electrode datasets.

This repository is **not** a new Bayesian optimization algorithm. It is a practical audit-and-replay workflow for asking whether a messy literature-derived materials database can support active-learning-style prioritization under realistic constraints:

- paper-level leakage from multiple samples in the same publication;
- protocol confounding from current density, voltage window, electrolyte, mass loading, and cycle number;
- missing descriptors such as BET, `d002`, `ID/IG`, heteroatom content, and pore volume;
- AI-extraction errors and suspicious high-performance outliers;
- quality-tier ablation before trusting BO/ML conclusions.

The included demo dataset is **synthetic** and only exists to test the scripts. Replace it with your own verified SIB/LIB/aqueous-SC database before making scientific claims.

## Repository layout

```text
carbon-literature-bo-replay-skill/
├── .agents/skills/carbon-literature-bo-replay/  # Codex skill
├── scripts/                                     # deterministic audit/replay scripts
├── schemas/                                     # JSON schemas for data and reports
├── configs/                                     # replay config templates
├── examples/sib_hard_carbon_synthetic/          # synthetic runnable example
├── data/raw/                                    # put your real CSV/XLSX here
├── data/curated/                                # cleaned intermediate files
├── data/modeling_ready/                         # ML/BO-ready exports
└── outputs/                                     # generated reports and curves
```

## Install

```bash
pip install -r requirements.txt
```

## Run the synthetic demo

```bash
python scripts/run_pipeline.py \
  --input examples/sib_hard_carbon_synthetic/synthetic_sib_hard_carbon.csv \
  --target ice_percent \
  --outdir outputs/synthetic_demo
```

Expected outputs:

```text
outputs/synthetic_demo/
├── audit_report.md
├── audit_tables/
├── modeling_ready.csv
├── model_metrics.csv
├── bo_replay_curves.csv
├── bo_replay_summary.md
├── bo_replay_curve.png
├── top_candidate_queue.csv
└── source_pdf_recheck_queue.csv
```

## Use your real dataset

Put your dataset in `data/raw/`, for example:

```text
data/raw/sib_hard_carbon_real.csv
```

Then run:

```bash
python scripts/run_pipeline.py \
  --input data/raw/sib_hard_carbon_real.csv \
  --target ice_percent \
  --outdir outputs/sib_real_ice
```

## Minimal required columns

The scripts expect these columns. Extra columns are preserved.

```text
sample_id, paper_id, year, material_system, device_system, precursor,
carbonization_temperature_c, bet_m2_g, d002_nm, id_ig, n_at_percent, o_at_percent,
electrolyte, current_density_mag, mass_loading_mg_cm2, voltage_window,
ice_percent, reversible_capacity_mah_g, source_location, doi,
quality_tier, needs_manual_check
```

A template is provided at:

```text
.agents/skills/carbon-literature-bo-replay/assets/templates/dataset_template.csv
```

## Dataset release policy for unfinished manuscripts

If your review manuscript or database paper is not finished, do **not** upload the full real literature database. Use this release pattern instead:

1. Public: synthetic demo dataset and schema/templates.
2. Private: normalized real modeling table for local testing.
3. Later release: verified real subset only after manuscript/database freeze.

A public synthetic SIB demo generated for this version is available at:

```text
examples/sib_hard_carbon_public_demo/sib_hard_carbon_public_synthetic_demo_80.csv
```

To convert a Chinese-header SIB workbook into the normalized schema for local/private testing:

```bash
python scripts/convert_sib_chinese_workbook.py \
  --input data/raw/SIB_all_samples.xlsx \
  --sheet Sheet1 \
  --output data/modeling_ready/sib_internal_modeling_ready.csv
```

For a main-analysis subset only:

```bash
python scripts/convert_sib_chinese_workbook.py \
  --input data/raw/SIB_all_samples.xlsx \
  --sheet Sheet1 \
  --main-only \
  --output data/modeling_ready/sib_internal_main_subset.csv
```

See:

```text
.agents/skills/carbon-literature-bo-replay/references/dataset_release_policy.md
```

## Scientific caution

Do not claim new-material discovery from this workflow alone. Offline replay only evaluates whether a historical literature database can support prioritization. A real closed loop requires new synthesis, characterization, and electrochemical testing after each recommendation.

## Suggested GitHub description

> Data-quality-aware offline Bayesian optimization replay for literature-derived biomass carbon electrode databases.
