# Dataset release policy for `carbon-literature-bo-replay-skill`

Generated from the uploaded SIB workbook on 2026-06-21.

## Recommendation

Because the review manuscript is not finished, **do not upload the full real SIB/LIB/SC database to GitHub yet**.

Use a three-tier release strategy:

| Tier | File type | GitHub now? | Rationale |
|---|---:|---:|---|
| Public synthetic demo | Structure-preserving synthetic CSV with no real DOI/title/sample identity | Yes | Runs the workflow and demonstrates missingness, quality tiers, leakage checks and BO replay without exposing unpublished curation work |
| Public schema/template | Empty or synthetic row templates, field dictionary, quality-tier dictionary | Yes | Lets others adapt the skill |
| Internal real modeling table | Normalized rows from your uploaded workbook | No | Use locally to test scripts and prepare the manuscript; release only after the review/database version is frozen |

## What can be public now

Recommended GitHub public files:

```text
examples/sib_hard_carbon_public_demo/sib_hard_carbon_public_synthetic_demo_80.csv
references/dataset_release_policy.md
.agents/skills/carbon-literature-bo-replay/assets/templates/dataset_template.csv
```

The public demo dataset is explicitly marked as `dataset_type = synthetic_public_demo`.

## What should stay private now

Do **not** upload these before manuscript freeze:

```text
SIB_internal_modeling_ready_from_uploaded_DO_NOT_UPLOAD.csv
SIB_internal_main_carbonate_subset_DO_NOT_UPLOAD.csv
```

Reason: these files contain the real data extraction/curation work that supports the unfinished review.

## Recommended wording in README

> The included public demo dataset is synthetic and is provided only to test the audit/replay workflow. The real literature-derived SIB/LIB/aqueous-SC databases remain under active curation and are not released in this version.

## Release after manuscript freeze

After manuscript submission or database freeze, a small real verified subset can be released if it satisfies all of the following:

1. Every row has DOI or stable source identifier.
2. Every row has source location such as `Fig. 3b`, `Table S2`, or SI table.
3. Units are standardized.
4. `quality_tier` is assigned.
5. Rows used in the manuscript match the released version.
6. Any figure-extracted/estimated values are explicitly flagged.
