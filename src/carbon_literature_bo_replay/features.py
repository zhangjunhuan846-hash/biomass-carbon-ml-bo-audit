from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd

# Conservative default: performance-derived columns are excluded unless the user explicitly
# passes them through --features and accepts the scientific risk.
TARGET_LIKE = re.compile(
    r"target|ice|capacity|capacitance|retention|performance|best|rank|score|"
    r"coulombic|efficiency|energy|power|rate|prediction|predicted|label",
    re.I,
)
PROTECTED = {
    "sample_id",
    "paper_id",
    "doi",
    "source",
    "reference",
    "journal",
    "year",
    "note",
    "notes",
    "material_name",
    "sample_name",
}


def _excluded_columns(target: str, id_col: str | None = None, paper_col: str | None = None) -> set[str]:
    excluded = {target}
    if id_col:
        excluded.add(id_col)
    if paper_col:
        excluded.add(paper_col)
    return excluded


def select_numeric_features(
    df: pd.DataFrame,
    target: str,
    id_col: str | None = None,
    paper_col: str | None = None,
    max_missing: float = 0.60,
) -> tuple[list[str], list[dict]]:
    """Select numeric descriptor columns with conservative leakage protection.

    The automatic selector is intentionally strict. In literature-derived materials
    datasets, columns such as capacity, retention, ranking, score, or predicted_* often
    encode the target itself or a competing performance endpoint. They are excluded by
    default and reported in the issue list.
    """

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found")
    if not 0 <= max_missing < 1:
        raise ValueError("max_missing must be in [0, 1)")

    excluded = _excluded_columns(target, id_col, paper_col)
    issues: list[dict] = []
    features: list[str] = []

    for col in df.select_dtypes(include="number").columns:
        lower = col.lower().strip()
        if col in excluded or lower in PROTECTED:
            continue
        if TARGET_LIKE.search(col):
            issues.append(
                {
                    "column": col,
                    "risk": "P1",
                    "reason": "Column name looks target/performance-derived; excluded to reduce leakage.",
                }
            )
            continue
        missing = float(df[col].isna().mean())
        if missing > max_missing:
            issues.append(
                {
                    "column": col,
                    "risk": "P2",
                    "reason": f"High missingness ({missing:.1%}); excluded from default feature set.",
                }
            )
            continue
        features.append(col)

    return features, issues


def validate_requested_features(df: pd.DataFrame, requested: Iterable[str], target: str) -> tuple[list[str], list[dict]]:
    """Validate user-supplied feature names and return accepted features plus issues."""

    accepted: list[str] = []
    issues: list[dict] = []
    for feature in requested:
        if feature == target:
            issues.append({"column": feature, "risk": "P0", "reason": "Target column cannot be used as a feature."})
            continue
        if feature not in df.columns:
            issues.append({"column": feature, "risk": "P1", "reason": "Requested feature was not found in the dataset."})
            continue
        if not pd.api.types.is_numeric_dtype(df[feature]):
            issues.append({"column": feature, "risk": "P1", "reason": "Requested feature is not numeric."})
            continue
        accepted.append(feature)
    return accepted, issues


def make_xy(df: pd.DataFrame, features: list[str], target: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Build a complete-case design matrix for replay."""

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found")
    if not features:
        raise ValueError("No usable numeric descriptor features were selected. Pass --features or clean the dataset.")

    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Feature columns not found: {missing}")

    data = df[features + [target]].replace([np.inf, -np.inf], np.nan).copy()
    for col in features + [target]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna().copy()

    if len(data) < 3:
        raise ValueError("Fewer than 3 complete cases remain after dropping missing feature/target values.")

    x = data[features].to_numpy(dtype=float)
    y = data[target].to_numpy(dtype=float)
    return data, x, y
