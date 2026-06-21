from __future__ import annotations

import re
import pandas as pd

TARGET_LIKE = re.compile(r"target|ice|capacity|capacitance|retention|performance|best|rank|score", re.I)
PROTECTED = {"sample_id", "paper_id", "doi", "source", "note", "material_name", "sample_name"}


def select_numeric_features(df: pd.DataFrame, target: str, id_col: str | None = None, paper_col: str | None = None) -> tuple[list[str], list[dict]]:
    excluded = {target}
    if id_col:
        excluded.add(id_col)
    if paper_col:
        excluded.add(paper_col)
    issues: list[dict] = []
    features: list[str] = []
    for col in df.select_dtypes(include="number").columns:
        lower = col.lower()
        if col in excluded or lower in PROTECTED:
            continue
        if TARGET_LIKE.search(col) and col != target:
            issues.append({"column": col, "risk": "P1", "reason": "Column name looks target/performance-derived; excluded to reduce leakage."})
            continue
        if df[col].isna().mean() > 0.6:
            issues.append({"column": col, "risk": "P2", "reason": "High missingness; excluded from default feature set."})
            continue
        features.append(col)
    return features, issues


def make_xy(df: pd.DataFrame, features: list[str], target: str):
    data = df[features + [target]].dropna().copy()
    x = data[features].to_numpy(dtype=float)
    y = data[target].to_numpy(dtype=float)
    return data, x, y
