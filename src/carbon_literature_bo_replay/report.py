from __future__ import annotations

from pathlib import Path
import pandas as pd


def decision_from(summary: dict, leakage: dict) -> str:
    if leakage.get("risk_level") == "HIGH":
        return "STOP"
    if summary.get("n_rounds", 0) < 5:
        return "METHOD_ONLY"
    if summary.get("improvement_over_random", 0) > 0:
        return "GO_EXPERIMENT"
    return "GO_MORE_DATA"


def write_report(path: str | Path, profile: dict, features: list[str], summary: dict, leakage: dict) -> None:
    decision = decision_from(summary, leakage)
    text = f"""# Offline BO Replay Report

## Decision

**{decision}**

## Scientific boundary

This is an offline literature replay. It evaluates whether a search policy can locate already-reported high-performing samples faster than baselines. It does not prove discovery of a new material.

## Dataset profile

- Samples: {profile.get('n_rows')}
- Target: `{profile.get('target')}`
- Numeric feature candidates: {len(profile.get('numeric_features', []))}
- Selected features: {len(features)}
- Papers: {profile.get('n_papers')}

## Selected descriptors

{chr(10).join('- `' + f + '`' for f in features)}

## Replay summary

- Final BO best: {summary.get('final_bo_best'):.4g}
- Final random mean best: {summary.get('final_random_mean_best'):.4g}
- Improvement over random: {summary.get('improvement_over_random'):.4g}
- Rounds: {summary.get('n_rounds')}

## Leakage and validity audit

- Risk level: **{leakage.get('risk_level')}**
- Issues: {len(leakage.get('issues', []))}

## Recommended wording

离线文献回放结果提示，在当前描述符空间和候选池定义下，BO-style acquisition 相比随机搜索的搜索效率为：`{summary.get('improvement_over_random'):.4g}`。该结果可作为后续实验闭环设计的依据，但不应被表述为新材料发现。
"""
    Path(path).write_text(text, encoding="utf-8")
