# Field dictionary

| Column | Meaning | Unit / values | Notes |
|---|---|---|---|
| `sample_id` | sample-level identifier | string | Must be unique. |
| `paper_id` | publication-level identifier | string | Required for leakage checks. |
| `year` | publication year | integer | Used for time-split analysis. |
| `doi` | DOI or stable source ID | string | Do not fabricate. |
| `source_location` | table/figure/page location | string | Example: `Table 1`, `Fig. 3b`, `SI Table S2`. |
| `material_system` | material class | string | Example: biomass hard carbon. |
| `device_system` | application | `SIB`, `LIB`, `aqueous_SC` | Do not mix without stratification. |
| `precursor` | biomass/carbon precursor | string | Normalize synonyms carefully. |
| `carbonization_temperature_c` | final carbonization temperature | °C | Numeric. |
| `activation_method` | activation/etching method | string | Example: KOH, CO2, none. |
| `bet_m2_g` | BET surface area | m²/g | High BET may help SC but harm ICE in batteries. |
| `total_pore_volume_cm3_g` | pore volume | cm³/g | Optional but useful. |
| `d002_nm` | interlayer spacing | nm | From XRD. |
| `id_ig` | Raman ID/IG | dimensionless | Specify if peak fitting differs. |
| `n_at_percent` | nitrogen content | at.% | Prefer XPS atomic percent. |
| `o_at_percent` | oxygen content | at.% | Prefer XPS atomic percent. |
| `electrolyte` | electrolyte system | string | Required for SIB/LIB interpretability. |
| `current_density_mag` | current density | mA/g | Normalize A/g to mA/g. |
| `mass_loading_mg_cm2` | electrode mass loading | mg/cm² | Missingness is a major engineering-risk flag. |
| `voltage_window` | test voltage window | string | Keep raw string if parsing is uncertain. |
| `ice_percent` | initial Coulombic efficiency | % | Main SIB hard-carbon target. |
| `reversible_capacity_mah_g` | reversible capacity | mAh/g | Protocol-dependent. |
| `specific_capacitance_f_g` | capacitance | F/g | SC target; device configuration matters. |
| `quality_tier` | curation confidence | `Tier0`, `Tier1`, `Tier2`, `Tier3` | See quality-tier reference. |
| `needs_manual_check` | manual recheck flag | yes/no | Use for source-PDF triage. |
| `check_reason` | reason for recheck | string | Keep concise. |
