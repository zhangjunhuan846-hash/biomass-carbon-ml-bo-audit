from __future__ import annotations

import re
import pandas as pd

TARGET_LIKE = re.compile(r"target|ice|capacity|capacitance|retention|performance|best|rank|score", re.I)


def audit_leakage(df: pd.DataFrame, target: str, features: list[str], paper_col: str | None = None) -> tuple[pd.DataFrame, dict]:
    issues: list[dict] = []
    for f in features:
        if TARGET_LIKE.search(f) and f != target:
            issues.append({"risk": "HIGH", "type": "target_like_feature", "field": f, "message": "Feature name may encode target/performance information."})
    if len(df) < 30:
        issues.append({"risk": "MEDIUM", "type": "low_n", "field": "dataset", "message": "Dataset has fewer than 30 samples; use as method demonstration only."})
    if paper_col and paper_col in df.columns:
        papers = df[paper_col].value_counts()
        dominant = papers.iloc[0] / len(df)
        if dominant > 0.25:
            issues.append({"risk": "MEDIUM", "type": "dominant_paper", "field": paper_col, "message": "One paper contributes more than 25% of samples; search efficiency may be inflated."})
    risk_level = "HIGH" if any(i["risk"] == "HIGH" for i in issues) else "MEDIUM" if issues else "LOW"
    return pd.DataFrame(issues), {"risk_level": risk_level, "issues": issues}
