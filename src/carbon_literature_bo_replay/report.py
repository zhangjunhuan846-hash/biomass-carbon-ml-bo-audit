from __future__ import annotations

from pathlib import Path


def decision_from(summary: dict, leakage: dict) -> str:
    """Return a conservative decision label for research use."""

    if leakage.get("risk_level") == "HIGH":
        return "STOP"
    if summary.get("n_rounds", 0) < 5:
        return "METHOD_ONLY"
    if summary.get("beats_random_mean") and summary.get("auc_improvement_over_random", 0) > 0:
        return "GO_EXPERIMENT" if leakage.get("risk_level") == "LOW" else "GO_MORE_DATA"
    return "GO_MORE_DATA"


def _feature_lines(features: list[str]) -> str:
    return "\n".join("- `" + f + "`" for f in features) if features else "- No valid descriptors selected."


def write_report(path: str | Path, profile: dict, features: list[str], summary: dict, leakage: dict) -> None:
    decision = decision_from(summary, leakage)
    direction = summary.get("direction", "maximize")
    text = f"""# Offline BO Replay Report

## Decision

**{decision}**

## Scientific boundary

This is an offline literature replay. It evaluates whether a search policy can locate already-reported high-performing samples faster than baselines under a fixed dataset, descriptor space, and replay protocol. It does not prove discovery of a new material.

## Dataset profile

- Samples: {profile.get('n_rows')}
- Target: `{profile.get('target')}`
- Direction: `{direction}`
- Numeric feature candidates: {len(profile.get('numeric_features', []))}
- Selected features: {len(features)}
- Papers/groups: {profile.get('n_papers')}

## Selected descriptors

{_feature_lines(features)}

## Replay summary

- Final BO best: {summary.get('final_bo_best'):.4g}
- Final random mean best: {summary.get('final_random_mean_best'):.4g}
- Final random p10 / p90: {summary.get('final_random_p10'):.4g} / {summary.get('final_random_p90'):.4g}
- Final improvement over random mean: {summary.get('improvement_over_random'):.4g}
- AUC improvement over random mean: {summary.get('auc_improvement_over_random'):.4g}
- Rounds: {summary.get('n_rounds')}

## Leakage and validity audit

- Risk level: **{leakage.get('risk_level')}**
- Issues: {len(leakage.get('issues', []))}

## Interpretation rule

- `GO_EXPERIMENT`: offline replay is promising enough to justify a small real experimental loop.
- `GO_MORE_DATA`: the idea is plausible, but the database or grouping/coverage is not yet strong enough.
- `METHOD_ONLY`: use only as a reproducible workflow demonstration.
- `STOP`: leakage or target-definition risk is too high.

## Recommended wording

离线文献回放结果提示，在当前描述符空间、候选池和回放协议下，BO-style acquisition 相比随机搜索的最终最优值提升为 `{summary.get('improvement_over_random'):.4g}`，AUC 提升为 `{summary.get('auc_improvement_over_random'):.4g}`。该结果可作为后续小规模实验闭环设计的依据，但不应被表述为新材料发现。
"""
    Path(path).write_text(text, encoding="utf-8")
