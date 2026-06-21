# Workflow reference

## Core idea

The workflow tests whether a heterogeneous literature-derived materials database supports active-learning-style prioritization. It does not validate a new synthesis route.

## Stages

1. **Data intake**: load CSV/XLSX, normalize common column names, preserve all original columns.
2. **Audit**: missingness, duplicate samples, paper-level clustering, protocol completeness, suspicious outliers.
3. **Modeling-ready export**: numeric feature matrix, explicit exclusions, quality flags.
4. **Baselines**: median, RF/ExtraTrees, optional gradient boosting.
5. **Offline BO replay**: historical reveal simulation using model uncertainty.
6. **Leakage stress test**: compare random split with paper-aware or time-aware alternatives.
7. **Recheck queue**: prioritize samples whose values strongly affect conclusions.
8. **Report**: P0/P1/P2 risks and scientific interpretation.

## Recommended interpretation scale

- **Ready for exploratory BO replay**: target is sufficiently populated, paper IDs exist, protocol fields are mostly present, and no single paper dominates top candidates.
- **ML screening only**: data can rank candidates but leakage/protocol risks remain high.
- **Curation first**: missingness, source ambiguity, or target inconsistency invalidates replay.
