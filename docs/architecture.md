# Architecture

The workflow is intentionally JSON-first. LLM agents should not repeatedly read the full dataset. The Python executor generates compact state files, and human/LLM agents can inspect only the relevant state file for each decision.

Core state files:

- `01_dataset_profile.json`
- `02_descriptor_schema.json`
- `03_replay_protocol.json`
- `04_surrogate_diagnostics.json`
- `05_acquisition_trace.json`
- `06_baseline_comparison.json`
- `07_leakage_audit.json`

The final report must preserve the scientific boundary between offline replay and real closed-loop discovery.
