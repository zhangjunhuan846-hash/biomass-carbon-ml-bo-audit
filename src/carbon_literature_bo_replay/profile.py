from __future__ import annotations

import pandas as pd


def profile_dataset(df: pd.DataFrame, target: str, id_col: str | None = None, paper_col: str | None = None) -> dict:
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found")
    numeric = [c for c in df.select_dtypes(include="number").columns if c != target]
    missing = {c: float(df[c].isna().mean()) for c in df.columns}
    warnings: list[str] = []
    if len(df) < 30:
        warnings.append("LOW_N: fewer than 30 samples; offline BO replay is method demonstration only.")
    if len(numeric) < 3:
        warnings.append("LOW_FEATURE_COUNT: fewer than 3 numeric descriptors available.")
    if df[target].isna().any():
        warnings.append("TARGET_MISSING: target column contains missing values.")
    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns),
        "target": target,
        "id_col": id_col,
        "paper_col": paper_col,
        "numeric_features": numeric,
        "missing_rate": missing,
        "n_papers": int(df[paper_col].nunique()) if paper_col and paper_col in df.columns else None,
        "target_summary": {
            "min": float(df[target].min()),
            "median": float(df[target].median()),
            "max": float(df[target].max()),
            "mean": float(df[target].mean()),
        },
        "warnings": warnings,
    }
