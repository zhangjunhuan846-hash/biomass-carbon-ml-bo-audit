from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_replay(trace: pd.DataFrame, baseline_summary: pd.DataFrame, outpath: str | Path) -> None:
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(trace["round"], trace["best_so_far"], marker="o", label="BO replay")
    ax.plot(baseline_summary["round"], baseline_summary["random_mean"], marker="s", label="Random mean")
    if {"random_p10", "random_p90"}.issubset(baseline_summary.columns):
        ax.fill_between(
            baseline_summary["round"],
            baseline_summary["random_p10"],
            baseline_summary["random_p90"],
            alpha=0.2,
            label="Random p10-p90",
        )
    optional = [
        ("exploit_best", "Exploit-only"),
        ("diversity_best", "Diversity"),
        ("oracle_best", "Oracle upper bound"),
    ]
    for column, label in optional:
        if column in baseline_summary.columns:
            ax.plot(baseline_summary["round"], baseline_summary[column], marker=".", label=label)
    ax.set_xlabel("Replay round")
    ax.set_ylabel("Best target found")
    ax.set_title("Offline BO replay curve")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    plt.close(fig)
