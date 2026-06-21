from __future__ import annotations

import re

import numpy as np
import pandas as pd

TARGET_LIKE = re.compile(
    r"target|ice|capacity|capacitance|retention|performance|best|rank|score|"
    r"coulombic|efficiency|prediction|predicted|label",
    re.I,
)


def audit_leakage(df: pd.DataFrame, target: str, features: list[str], paper_col: str | None = None) -> tuple[pd.DataFrame, dict]:
    issues: list[dict] = []

    for f in features:
        if f not in df.columns:
            issues.append({"risk": "HIGH", "type": "missing_feature", "field": f, "message": "Selected feature is absent from the dataframe."})
            continue
        if TARGET_LIKE.search(f) and f != target:
            issues.append(
                {
                    "risk": "HIGH",
                    "type": "target_like_feature",
                    "field": f,
                    "message": "Feature name may encode target/performance information.",
                }
            )

    if len(df) < 30:
        issues.append(
            {
                "risk": "MEDIUM",
                "type": "low_n",
                "field": "dataset",
                "message": "Dataset has fewer than 30 samples; use as method demonstration only.",
            }
        )

    if target in df.columns:
        target_num = pd.to_numeric(df[target], errors="coerce")
        if target_num.notna().sum() < len(df) * 0.80:
            issues.append(
                {
                    "risk": "HIGH",
                    "type": "target_quality",
                    "field": target,
                    "message": "More than 20% of target values are missing or non-numeric.",
                }
            )
        for f in features:
            if f in df.columns:
                fnum = pd.to_numeric(df[f], errors="coerce")
                pair = pd.DataFrame({"x": fnum, "y": target_num}).replace([np.inf, -np.inf], np.nan).dropna()
                if len(pair) >= 8 and pair["x"].nunique() > 1 and pair["y"].nunique() > 1:
                    corr = float(pair["x"].corr(pair["y"]))
                    if abs(corr) >= 0.98:
                        issues.append(
                            {
                                "risk": "HIGH",
                                "type": "near_duplicate_target",
                                "field": f,
                                "message": f"Feature is almost perfectly correlated with target (Pearson r={corr:.3f}); check for derived leakage.",
                            }
                        )

    if paper_col:
        if paper_col in df.columns:
            papers = df[paper_col].value_counts(dropna=True)
            if not papers.empty:
                dominant = float(papers.iloc[0] / len(df))
                if dominant > 0.25:
                    issues.append(
                        {
                            "risk": "MEDIUM",
                            "type": "dominant_paper",
                            "field": paper_col,
                            "message": "One paper contributes more than 25% of samples; search efficiency may be inflated.",
                        }
                    )
                if len(papers) < 5:
                    issues.append(
                        {
                            "risk": "MEDIUM",
                            "type": "low_group_count",
                            "field": paper_col,
                            "message": "Fewer than 5 paper/groups are present; group leakage cannot be stress-tested robustly.",
                        }
                    )
        else:
            issues.append(
                {
                    "risk": "MEDIUM",
                    "type": "missing_group_column",
                    "field": paper_col,
                    "message": "Requested paper/group column was not found; same-paper leakage audit is disabled.",
                }
            )

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        issues.append(
            {
                "risk": "MEDIUM",
                "type": "duplicate_rows",
                "field": "dataset",
                "message": f"Detected {duplicate_count} fully duplicated rows; remove duplicates before making search-efficiency claims.",
            }
        )

    risk_level = "HIGH" if any(i["risk"] == "HIGH" for i in issues) else "MEDIUM" if issues else "LOW"
    return pd.DataFrame(issues, columns=["risk", "type", "field", "message"]), {"risk_level": risk_level, "issues": issues}
