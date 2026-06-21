from __future__ import annotations

import numpy as np
import pandas as pd
from .surrogate import RidgeSurrogate


def _choose_seed(y: np.ndarray, seed_size: int, rng: np.random.Generator) -> list[int]:
    seed_size = min(seed_size, len(y) - 1)
    return list(rng.choice(np.arange(len(y)), size=seed_size, replace=False))


def run_ucb_replay(data: pd.DataFrame, x: np.ndarray, y: np.ndarray, seed_size: int = 8, iterations: int = 20, beta: float = 0.5, random_state: int = 42) -> tuple[pd.DataFrame, list[int]]:
    rng = np.random.default_rng(random_state)
    observed = _choose_seed(y, seed_size, rng)
    remaining = [i for i in range(len(y)) if i not in observed]
    rows = []
    best_so_far = float(np.max(y[observed]))
    selected_order = []
    for r in range(1, min(iterations, len(remaining)) + 1):
        model = RidgeSurrogate().fit(x[observed], y[observed])
        mean, std = model.predict(x[remaining])
        score = mean + beta * std
        j = int(np.argmax(score))
        chosen = remaining.pop(j)
        observed.append(chosen)
        selected_order.append(chosen)
        best_so_far = max(best_so_far, float(y[chosen]))
        rows.append({
            "round": r,
            "chosen_index": int(chosen),
            "chosen_target": float(y[chosen]),
            "predicted_mean": float(mean[j]),
            "predicted_uncertainty": float(std[j]),
            "acquisition_score": float(score[j]),
            "best_so_far": best_so_far,
        })
    return pd.DataFrame(rows), selected_order


def run_random_baseline(y: np.ndarray, seed_size: int = 8, iterations: int = 20, repeats: int = 50, random_state: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    all_rows = []
    n = len(y)
    for rep in range(repeats):
        order = list(rng.choice(np.arange(n), size=n, replace=False))
        observed = order[:seed_size]
        pool = order[seed_size:]
        best = float(np.max(y[observed]))
        for r, idx in enumerate(pool[:iterations], start=1):
            best = max(best, float(y[idx]))
            all_rows.append({"repeat": rep, "round": r, "best_so_far": best})
    df = pd.DataFrame(all_rows)
    return df.groupby("round", as_index=False)["best_so_far"].agg(random_mean="mean", random_p10=lambda s: s.quantile(0.1), random_p90=lambda s: s.quantile(0.9))


def summarize_replay(trace: pd.DataFrame, random_summary: pd.DataFrame) -> dict:
    merged = trace.merge(random_summary, on="round", how="left")
    final = merged.iloc[-1]
    return {
        "final_bo_best": float(final["best_so_far"]),
        "final_random_mean_best": float(final["random_mean"]),
        "improvement_over_random": float(final["best_so_far"] - final["random_mean"]),
        "n_rounds": int(len(trace)),
    }
