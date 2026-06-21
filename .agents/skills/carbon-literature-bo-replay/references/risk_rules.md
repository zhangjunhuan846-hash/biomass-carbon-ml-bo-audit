# Risk rules

## P0 risks

- Selected target has fewer than 20 non-missing values.
- `paper_id` is absent and the user wants leakage-aware validation.
- Real data has no DOI/source-location fields.
- Target unit is ambiguous or mixed.
- Device systems are mixed without a `device_system` column.

## P1 risks

- One paper contributes more than 20% of usable samples.
- Random-split performance is much better than leave-one-paper-out performance.
- Top candidates mostly come from one paper.
- Current density or voltage window is missing for capacity/capacitance targets.
- Mass loading is mostly missing for engineering interpretation.
- BO superiority disappears after removing suspicious or Tier 2/3 samples.

## P2 risks

- Descriptor missingness limits feature interpretation.
- DOI present but source figure/table not specified.
- Quality-tier definitions are inconsistent.
- Feature importance is unstable across seeds.

## Suspicious sample heuristics

Flag samples for recheck when:

- target is above Q3 + 1.5 IQR;
- target is in top 5% and `source_location` is missing;
- high capacity/capacitance is reported at unusually high current density;
- very high BET and very high ICE coexist in SIB/LIB without electrolyte/protocol details;
- `needs_manual_check` is already yes;
- same `sample_id` or same descriptor-target signature appears more than once.
