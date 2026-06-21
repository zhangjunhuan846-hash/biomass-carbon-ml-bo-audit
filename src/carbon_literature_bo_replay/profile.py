from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_numeric_summary(s: pd.Series) -> dict:
    numeric = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric.empty:
        return {"min": None, "median": None, "max": None, "mean": None, "n_numeric": 0}
    return {
        "min": float(numeric.min()),
        "median": float(numeric.median()),
        "max": float(numeric.max()),
        "mean": float(numeric.mean()),
        "n_numeric": int(len(numeric)),
    }


def profile_dataset(df: pd.DataFrame, target: str, id_col: str | None = None, paper_col: str | None = None) -> dict:
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found")

    numeric = [c for c in df.select_dtypes(include="number").columns if c != target]
    missing = {c: float(df[c].isna().mean()) for c in df.columns}
    warnings: list[str] = []

    target_numeric = pd.to_numeric(df[target], errors="coerce")
    n_target_numeric = int(target_numeric.notna().sum())

    if len(df) < 30:
        warnings.append("LOW_N: fewer than 30 samples; offline BO replay is method demonstration only.")
    if len(numeric) < 3:
        warnings.append("LOW_FEATURE_COUNT: fewer than 3 numeric descriptors available.")
    if df[target].isna().any() or n_target_numeric < len(df):
        warnings.append("TARGET_MISSING_OR_NON_NUMERIC: target column contains missing or non-numeric values.")
    if paper_col and paper_col not in df.columns:
        warnings.append(f"PAPER_COL_MISSING: requested paper/group column '{paper_col}' was not found.")
    if id_col and id_col not in df.columns:
        warnings.append(f"ID_COL_MISSING: requested sample id column '{id_col}' was not found.")

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
        "target_summary": _safe_numeric_summary(df[target]),
        "warnings": warnings,
    }
