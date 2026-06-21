# carbon-literature-bo-replay-skill

Use this skill when the user wants to run, design, or audit an offline Bayesian optimization replay on a literature-derived chemical/materials dataset, especially for carbon materials, biomass-derived carbon, hard carbon, LIB/SIB/aqueous-SC samples, or AI4Materials candidate screening.

## Core intent

This skill is for **offline literature replay**, not for claiming real autonomous discovery. It evaluates whether a search policy finds already-reported high-performing samples faster than baselines under a fixed descriptor space and replay protocol.

## Inputs

- Literature-derived CSV/XLSX database.
- Target column such as ICE, reversible capacity, plateau capacity, capacitance, retention, impedance, or degradation rate.
- Descriptor columns such as BET, d002, ID/IG, XPS_N, XPS_O, carbonization temperature, pore volume, mass loading, electrode thickness, compacted density.
- Optional `sample_id` and `paper_id` / group column for auditability.

## Workflow

1. Profile the dataset and target quality.
2. Build a conservative descriptor schema.
3. Exclude target-like, performance-like, predicted-like, rank-like, and high-missingness fields unless explicitly justified.
4. Define replay protocol: seed size, rounds, random repeats, objective direction, and candidate pool.
5. Run UCB-style acquisition with a lightweight ridge surrogate.
6. Compare against random, exploit-only, diversity, and oracle upper-bound baselines.
7. Audit leakage and validity.
8. Produce a decision report: GO_EXPERIMENT, GO_MORE_DATA, METHOD_ONLY, or STOP.

## Mandatory scientific boundary

Always distinguish:

- offline literature replay;
- candidate prioritization;
- real experimental closed-loop optimization;
- new material discovery.

Do not describe the result as discovering a new material unless there is new experimental validation.

## Preferred wording

"The offline replay suggests that the acquisition strategy identifies already-reported high-performing literature samples more efficiently than random search under the defined descriptor space and replay protocol. The result supports candidate prioritization for a future experimental loop, but it should not be interpreted as autonomous discovery."
