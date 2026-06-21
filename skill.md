# carbon-literature-bo-replay-skill

Use this skill when the user wants to run, design, or audit an offline Bayesian optimization replay on a literature-derived chemical/materials dataset, especially for carbon materials, biomass-derived carbon, hard carbon, LIB/SIB/SC samples, or AI4Materials candidate screening.

## Core intent

This skill is for **offline literature replay**, not for claiming real autonomous discovery. It evaluates whether a search policy finds already-reported high-performing samples faster than baselines.

## Inputs

- Literature-derived CSV/XLSX database
- Target column such as ICE, capacity, capacitance, retention, or plateau capacity
- Descriptor columns such as BET, d002, ID/IG, XPS_N, XPS_O, carbonization temperature, pore volume, mass loading
- Optional paper_id or group column for leakage audit

## Workflow

1. Profile the dataset.
2. Build a descriptor schema.
3. Define replay protocol.
4. Run surrogate-assisted acquisition.
5. Compare against random, exploit-only, diversity, and oracle baselines.
6. Audit leakage and validity.
7. Produce a decision report.

## Mandatory scientific boundary

Always distinguish:

- offline literature replay
- candidate prioritization
- real experimental closed-loop optimization
- new material discovery

Do not describe the result as discovering a new material unless there is new experimental validation.
