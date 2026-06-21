# Multi-agent protocol

This skill uses JSON-first multi-agent execution to reduce token usage and preserve auditable intermediate states.

## Agents

### 01 Dataset Profile Agent
Reads the raw dataset once and writes `state/01_dataset_profile.json`.

### 02 Descriptor Schema Agent
Selects valid descriptors, excludes leakage columns, and writes `state/02_descriptor_schema.json`.

### 03 Replay Protocol Agent
Defines seed size, candidate pool, iterations, and baseline repeats. Writes `state/03_replay_protocol.json`.

### 04 Surrogate Agent
Fits or configures the surrogate model and writes `state/04_surrogate_diagnostics.json`.

### 05 Acquisition Replay Agent
Runs the offline acquisition loop and writes `state/05_acquisition_trace.json` plus `replay_trace.csv`.

### 06 Baseline Comparison Agent
Runs random/exploit/diversity baselines and writes `state/06_baseline_comparison.json`.

### 07 Leakage Validity Agent
Audits target leakage, same-paper leakage, duplicate samples, and low-n risks. Writes `state/07_leakage_audit.json`.

### 08 Report Agent
Writes `bo_replay_report.md` and gives GO_EXPERIMENT / GO_MORE_DATA / METHOD_ONLY / STOP.

## JSON packet rule

Each agent should read only:

- its direct input JSON packet;
- the minimal CSV file if numerical computation is required;
- the output JSON from upstream agents.

Avoid sending the full dataset or full manuscript text repeatedly to LLM agents.
