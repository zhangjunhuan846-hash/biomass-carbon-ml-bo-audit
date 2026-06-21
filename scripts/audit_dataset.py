from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from utils import (
    read_table, ensure_columns, boolish_yes, target_outlier_flags,
    write_markdown_table, DEFAULT_FEATURES
)

CORE_COLUMNS = [
    "sample_id", "paper_id", "year", "doi", "source_location",
    "material_system", "device_system", "precursor", "carbonization_temperature_c",
    "activation_method", "bet_m2_g", "total_pore_volume_cm3_g", "d002_nm",
    "id_ig", "n_at_percent", "o_at_percent", "electrolyte", "current_density_mag",
    "mass_loading_mg_cm2", "voltage_window", "quality_tier", "needs_manual_check",
    "check_reason"
]

PROTOCOL_COLUMNS = ["electrolyte", "current_density_mag", "mass_loading_mg_cm2", "voltage_window"]


def audit_dataframe(df: pd.DataFrame, target: str) -> dict[str, pd.DataFrame | str | int | float]:
    df = ensure_columns(df, CORE_COLUMNS + [target])
    n_rows = len(df)
    nonmissing_target = int(df[target].notna().sum()) if target in df.columns else 0

    missingness = pd.DataFrame({
        "column": df.columns,
        "missing_count": df.isna().sum().values,
        "missing_percent": (df.isna().mean().values * 100).round(1)
    }).sort_values(["missing_percent", "column"], ascending=[False, True])

    duplicates = pd.DataFrame()
    if "sample_id" in df.columns:
        dup_mask = df["sample_id"].notna() & df["sample_id"].duplicated(keep=False)
        duplicates = df.loc[dup_mask, [c for c in ["sample_id", "paper_id", target, "doi", "source_location"] if c in df.columns]].copy()

    paper_counts = pd.DataFrame()
    if "paper_id" in df.columns:
        paper_counts = df.groupby("paper_id", dropna=False).size().reset_index(name="n_samples").sort_values("n_samples", ascending=False)

    protocol_completeness = pd.DataFrame({
        "protocol_field": [c for c in PROTOCOL_COLUMNS if c in df.columns],
        "nonmissing_count": [int(df[c].notna().sum()) for c in PROTOCOL_COLUMNS if c in df.columns],
        "nonmissing_percent": [round(float(df[c].notna().mean()*100), 1) for c in PROTOCOL_COLUMNS if c in df.columns]
    })

    quality_counts = pd.DataFrame()
    if "quality_tier" in df.columns:
        quality_counts = df["quality_tier"].fillna("missing").value_counts(dropna=False).reset_index()
        quality_counts.columns = ["quality_tier", "n_samples"]

    outlier_mask = target_outlier_flags(df, target)
    manual_mask = boolish_yes(df["needs_manual_check"]) if "needs_manual_check" in df.columns else pd.Series(False, index=df.index)
    missing_source_mask = df["source_location"].isna() | (df["source_location"].astype("string").str.strip() == "")
    suspicious_mask = outlier_mask | manual_mask | (outlier_mask & missing_source_mask)

    recheck_cols = [c for c in [
        "sample_id", "paper_id", "year", "device_system", "precursor", target,
        "current_density_mag", "mass_loading_mg_cm2", "electrolyte", "quality_tier",
        "needs_manual_check", "check_reason", "doi", "source_location"
    ] if c in df.columns]
    recheck_queue = df.loc[suspicious_mask, recheck_cols].copy()
    if target in recheck_queue.columns:
        recheck_queue = recheck_queue.sort_values(target, ascending=False, na_position="last")

    risks = []
    if target not in df.columns or nonmissing_target == 0:
        risks.append(("P0", f"Target `{target}` is absent or empty."))
    elif nonmissing_target < 20:
        risks.append(("P0", f"Only {nonmissing_target} non-missing target values; offline replay is not meaningful."))
    elif nonmissing_target < 50:
        risks.append(("P1", f"Only {nonmissing_target} non-missing target values; treat replay as exploratory."))
    if "paper_id" not in df.columns or df["paper_id"].isna().mean() > 0.2:
        risks.append(("P0", "`paper_id` is missing for many samples; paper-level leakage cannot be checked."))
    if "doi" in df.columns and "source_location" in df.columns:
        if (df["doi"].isna() | df["source_location"].isna()).mean() > 0.5:
            risks.append(("P1", "More than half of records lack DOI or source location; source-PDF recheck will be difficult."))
    if not paper_counts.empty and n_rows > 0:
        top_share = float(paper_counts["n_samples"].iloc[0] / n_rows)
        if top_share > 0.2:
            risks.append(("P1", f"The largest paper contributes {top_share:.1%} of samples; top-candidate leakage risk is high."))
    for col in PROTOCOL_COLUMNS:
        if col in df.columns and df[col].isna().mean() > 0.5:
            risks.append(("P1", f"Protocol field `{col}` is missing in more than half of records."))
    if len(recheck_queue) > max(5, 0.1 * n_rows):
        risks.append(("P1", f"{len(recheck_queue)} samples entered the source-PDF recheck queue."))
    if not risks:
        risks.append(("P2", "No blocking audit risk found by automated checks; still perform manual source QA for top candidates."))
    risk_df = pd.DataFrame(risks, columns=["severity", "finding"])

    modeling_ready = df.copy()
    if "automated_outlier_flag" not in modeling_ready.columns:
        modeling_ready["automated_outlier_flag"] = outlier_mask.map({True:"yes", False:"no"})
    if "automated_recheck_flag" not in modeling_ready.columns:
        modeling_ready["automated_recheck_flag"] = suspicious_mask.map({True:"yes", False:"no"})

    return {
        "n_rows": n_rows,
        "nonmissing_target": nonmissing_target,
        "missingness": missingness,
        "duplicates": duplicates,
        "paper_counts": paper_counts,
        "protocol_completeness": protocol_completeness,
        "quality_counts": quality_counts,
        "recheck_queue": recheck_queue,
        "risk_df": risk_df,
        "modeling_ready": modeling_ready,
    }


def write_audit_report(results: dict, target: str, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    tables_dir = outdir / "audit_tables"
    tables_dir.mkdir(exist_ok=True)
    for key in ["missingness", "duplicates", "paper_counts", "protocol_completeness", "quality_counts", "recheck_queue", "risk_df"]:
        obj = results.get(key)
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(tables_dir / f"{key}.csv", index=False)
    results["modeling_ready"].to_csv(outdir / "modeling_ready.csv", index=False)
    results["recheck_queue"].to_csv(outdir / "source_pdf_recheck_queue.csv", index=False)

    report = []
    report.append(f"# Dataset audit report\n")
    report.append(f"Target: `{target}`\n")
    report.append(f"Rows: **{results['n_rows']}**\n")
    report.append(f"Non-missing target values: **{results['nonmissing_target']}**\n")
    report.append("## P0/P1/P2 risk register\n")
    report.append(write_markdown_table(results["risk_df"], max_rows=30))
    report.append("\n## Missingness bottlenecks\n")
    report.append(write_markdown_table(results["missingness"].head(20), max_rows=20))
    report.append("\n## Paper-level sample concentration\n")
    report.append(write_markdown_table(results["paper_counts"].head(15), max_rows=15))
    report.append("\n## Protocol completeness\n")
    report.append(write_markdown_table(results["protocol_completeness"], max_rows=10))
    report.append("\n## Quality-tier distribution\n")
    report.append(write_markdown_table(results["quality_counts"], max_rows=10))
    report.append("\n## Source-PDF recheck queue preview\n")
    report.append(write_markdown_table(results["recheck_queue"].head(20), max_rows=20))
    report.append("\n## Decision guidance\n")
    if (results["risk_df"]["severity"] == "P0").any():
        report.append("**Curation first.** The automated audit found P0 risks that can invalidate modeling or replay.\n")
    elif (results["risk_df"]["severity"] == "P1").any():
        report.append("**Exploratory only.** Modeling/BO replay may be useful, but interpretation is sensitive to leakage, protocol, or data quality.\n")
    else:
        report.append("**Ready for exploratory offline BO replay, not discovery claims.**\n")
    (outdir / "audit_report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a literature-derived carbon-electrode dataset.")
    parser.add_argument("--input", required=True, help="CSV/XLSX input file")
    parser.add_argument("--sheet", default=None, help="Excel sheet name or index")
    parser.add_argument("--target", default="ice_percent", help="Target column")
    parser.add_argument("--outdir", default="outputs/audit", help="Output directory")
    args = parser.parse_args()
    sheet = int(args.sheet) if args.sheet and str(args.sheet).isdigit() else args.sheet
    df = read_table(args.input, sheet=sheet)
    results = audit_dataframe(df, args.target)
    write_audit_report(results, args.target, Path(args.outdir))
    print(f"Audit complete: {args.outdir}")


if __name__ == "__main__":
    main()
