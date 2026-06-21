# carbon-literature-bo-replay-skill

A Codex-friendly skill for **offline Bayesian optimization replay** on literature-derived carbon materials datasets.

It evaluates whether a BO-style acquisition policy can locate already-reported high-performing samples faster than random search, exploit-only selection, diversity sampling, and an oracle upper bound. It does **not** claim autonomous discovery of new materials.

## Install

```bash
pip install -r requirements.txt
pip install -e .
pytest -q
```

## Demo

```bash
python examples/run_demo.py
```

or:

```bash
python -m carbon_literature_bo_replay.cli replay \
  --data examples/input/carbon_literature_demo.csv \
  --target ICE \
  --id-col sample_id \
  --paper-col paper_id \
  --out outputs/demo_replay \
  --direction maximize
```

## Outputs

- `bo_replay_report.md`
- `replay_trace.csv`
- `baseline_comparison.csv`
- `recommended_candidates.csv`
- `leakage_audit.csv`
- `selected_features.csv`
- JSON-first state files under `state/`
- `figures/bo_replay_curve.png`

## Boundary statement

The offline replay may support candidate prioritization before a real experimental loop. It should not be described as discovery of a new material unless new experimental validation has been performed.
