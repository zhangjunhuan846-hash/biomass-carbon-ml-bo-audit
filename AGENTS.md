# Multi-agent protocol

This skill uses JSON-first multi-agent execution to reduce token usage and preserve auditable intermediate states.

## Agents

### 01 Dataset Profile Agent
Reads the raw dataset once and writes `state/01_dataset_profile.json`. Check sample count, target quality, missingness, available numeric fields, and paper/group count.

### 02 Descriptor Schema Agent
Selects valid descriptors, excludes leakage columns, and writes `state/02_descriptor_schema.json`. Default behavior must be conservative: exclude target-like, performance-like, prediction-like, score/rank-like, and high-missingness fields.

### 03 Replay Protocol Agent
Defines seed size, candidate pool, iterations, objective direction, and baseline repeats. Writes `state/03_replay_protocol.json`.

### 04 Surrogate Agent
Fits or configures the surrogate model and writes `state/04_surrogate_diagnostics.json`. The default implementation uses a dependency-light ridge surrogate with a distance-scaled residual uncertainty proxy.

### 05 Acquisition Replay Agent
Runs the offline acquisition loop and writes `state/05_acquisition_trace.json` plus `replay_trace.csv`.

### 06 Baseline Comparison Agent
Runs random, exploit-only, diversity, and oracle upper-bound baselines. Writes `baseline_comparison.csv` and `state/06_baseline_comparison.json`.

### 07 Leakage Validity Agent
Audits target leakage, same-paper concentration, low group count, duplicate rows, near-duplicate target features, and low-n risks. Writes `leakage_audit.csv` and `state/07_leakage_audit.json`.

### 08 Report Agent
Writes `bo_replay_report.md` and gives GO_EXPERIMENT / GO_MORE_DATA / METHOD_ONLY / STOP.

## JSON packet rule

Each agent should read only:

- its direct input JSON packet;
- the minimal CSV/XLSX file if numerical computation is required;
- the output JSON from upstream agents.

Avoid repeatedly sending the full dataset, manuscript, or source PDFs to LLM agents.

## Scientific boundary rule

Never convert offline replay wording into real discovery wording. The output is a candidate-prioritization and workflow-audit result unless new experimental validation is present.
