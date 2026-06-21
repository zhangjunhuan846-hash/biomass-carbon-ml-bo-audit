# Reporting standard

## Required report sections

1. Dataset identity and target.
2. Size, target coverage, and device-system composition.
3. Missingness bottlenecks.
4. Paper-level leakage risk.
5. Protocol confounding risk.
6. Model baseline results.
7. Offline BO replay results.
8. Top candidate queue.
9. Source-PDF recheck queue.
10. P0/P1/P2 decision.

## Standard conclusion language

Use one of:

- `Ready for exploratory offline BO replay, not for discovery claims.`
- `Usable for ML screening only; BO interpretation is leakage/protocol-sensitive.`
- `Curation first; current data quality is insufficient for meaningful replay.`

Avoid:

- `The model discovered new materials.`
- `BO proves the optimal synthesis condition.`
- `Feature importance proves mechanism.`
