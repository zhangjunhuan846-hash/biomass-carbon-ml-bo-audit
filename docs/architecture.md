# Architecture

The workflow is intentionally JSON-first. LLM agents should not repeatedly read the full dataset. The Python executor generates compact state files, and human/LLM agents can inspect only the relevant state file for each decision.

## Core pipeline

```text
raw dataset
  -> dataset profile
  -> descriptor schema
  -> replay protocol
  -> surrogate-assisted acquisition
  -> baseline comparison
  -> leakage/validity audit
  -> decision report
```

## Core state files

- `01_dataset_profile.json`
- `02_descriptor_schema.json`
- `03_replay_protocol.json`
- `04_surrogate_diagnostics.json`
- `05_acquisition_trace.json`
- `06_baseline_comparison.json`
- `07_leakage_audit.json`

## Baselines

- UCB-style BO replay: deployable offline policy being tested.
- Random search: lower reference baseline with repeated trials.
- Exploit-only: predicted mean only, no uncertainty bonus.
- Diversity: farthest-candidate sampling in standardized descriptor space.
- Oracle upper bound: non-deployable reference that uses the true target.

## Validity constraints

The final report must preserve the scientific boundary between offline replay and real closed-loop discovery. A strong offline curve is only a reason to design a small experimental loop; it is not itself material discovery.
