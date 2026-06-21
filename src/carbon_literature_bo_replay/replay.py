from __future__ import annotations

import numpy as np
import pandas as pd

from .surrogate import RidgeSurrogate


def _sign(direction: str) -> int:
    if direction not in {"maximize", "minimize"}:
        raise ValueError("direction must be 'maximize' or 'minimize'")
    return 1 if direction == "maximize" else -1


def _best(values: np.ndarray, direction: str) -> float:
    return float(np.max(values) if direction == "maximize" else np.min(values))


def _choose_seed(y: np.ndarray, seed_size: int, rng: np.random.Generator) -> list[int]:
    if len(y) < 3:
        raise ValueError("At least 3 complete samples are required for replay.")
    if seed_size < 2:
        raise ValueError("seed_size must be at least 2 for surrogate fitting.")
    seed_size = min(seed_size, len(y) - 1)
    return list(rng.choice(np.arange(len(y)), size=seed_size, replace=False))


def run_ucb_replay(
    data: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    seed_size: int = 8,
    iterations: int = 20,
    beta: float = 0.5,
    random_state: int = 42,
    direction: str = "maximize",
) -> tuple[pd.DataFrame, list[int]]:
    """Run a dependency-light UCB-style offline replay.

    The surrogate is fitted on a signed target. For minimization tasks, the internal
    acquisition maximizes ``-y`` but the reported target values remain in original units.
    """

    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    sgn = _sign(direction)
    y_model = sgn * y
    rng = np.random.default_rng(random_state)
    observed = _choose_seed(y, seed_size, rng)
    remaining = [i for i in range(len(y)) if i not in observed]
    rows: list[dict] = []
    best_so_far = _best(y[observed], direction)
    selected_order: list[int] = []

    for r in range(1, min(iterations, len(remaining)) + 1):
        model = RidgeSurrogate().fit(x[observed], y_model[observed])
        mean_signed, std = model.predict(x[remaining])
        score = mean_signed + beta * std
        j = int(np.argmax(score))
        chosen = remaining.pop(j)
        observed.append(chosen)
        selected_order.append(chosen)
        best_so_far = _best(y[observed], direction)
        rows.append(
            {
                "round": r,
                "chosen_index": int(chosen),
                "chosen_target": float(y[chosen]),
                "predicted_mean": float(sgn * mean_signed[j]),
                "predicted_uncertainty": float(std[j]),
                "acquisition_score": float(score[j]),
                "best_so_far": best_so_far,
            }
        )
    return pd.DataFrame(rows), selected_order


def run_random_baseline(
    y: np.ndarray,
    seed_size: int = 8,
    iterations: int = 20,
    repeats: int = 50,
    random_state: int = 0,
    direction: str = "maximize",
) -> pd.DataFrame:
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    rng = np.random.default_rng(random_state)
    all_rows: list[dict] = []
    n = len(y)
    _choose_seed(y, seed_size, rng=np.random.default_rng(random_state + 999))
    for rep in range(repeats):
        order = list(rng.choice(np.arange(n), size=n, replace=False))
        observed = order[: min(seed_size, n - 1)]
        pool = order[min(seed_size, n - 1) :]
        best = _best(y[observed], direction)
        for r, idx in enumerate(pool[:iterations], start=1):
            observed.append(idx)
            best = _best(y[observed], direction)
            all_rows.append({"repeat": rep, "round": r, "best_so_far": best})
    df = pd.DataFrame(all_rows)
    if df.empty:
        raise ValueError("No random-baseline rounds were produced. Reduce seed_size or check dataset size.")
    return df.groupby("round", as_index=False)["best_so_far"].agg(
        random_mean="mean",
        random_p10=lambda s: s.quantile(0.1),
        random_p90=lambda s: s.quantile(0.9),
    )


def run_diversity_baseline(
    x: np.ndarray,
    y: np.ndarray,
    seed_size: int = 8,
    iterations: int = 20,
    random_state: int = 42,
    direction: str = "maximize",
) -> pd.DataFrame:
    """Select candidates that are farthest from the observed set in standardized space."""

    rng = np.random.default_rng(random_state)
    observed = _choose_seed(y, seed_size, rng)
    remaining = [i for i in range(len(y)) if i not in observed]
    z = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-9)
    rows: list[dict] = []
    best = _best(y[observed], direction)
    for r in range(1, min(iterations, len(remaining)) + 1):
        distances = np.sqrt(((z[remaining, None, :] - z[observed][None, :, :]) ** 2).sum(axis=2))
        nearest = distances.min(axis=1)
        j = int(np.argmax(nearest))
        chosen = remaining.pop(j)
        observed.append(chosen)
        best = _best(y[observed], direction)
        rows.append({"round": r, "diversity_best": best, "diversity_chosen_index": int(chosen)})
    return pd.DataFrame(rows)


def run_oracle_baseline(
    y: np.ndarray,
    seed_size: int = 8,
    iterations: int = 20,
    random_state: int = 42,
    direction: str = "maximize",
) -> pd.DataFrame:
    """Upper bound that uses the true target to select the next candidate.

    This is not a deployable strategy. It is included only to show the maximum possible
    best-found curve for the same initial seed.
    """

    rng = np.random.default_rng(random_state)
    observed = _choose_seed(y, seed_size, rng)
    remaining = [i for i in range(len(y)) if i not in observed]
    order = sorted(remaining, key=lambda i: y[i], reverse=(direction == "maximize"))
    rows: list[dict] = []
    best = _best(y[observed], direction)
    for r, chosen in enumerate(order[:iterations], start=1):
        observed.append(chosen)
        best = _best(y[observed], direction)
        rows.append({"round": r, "oracle_best": best, "oracle_chosen_index": int(chosen)})
    return pd.DataFrame(rows)


def summarize_replay(trace: pd.DataFrame, random_summary: pd.DataFrame, direction: str = "maximize") -> dict:
    if trace.empty:
        raise ValueError("Replay trace is empty")
    merged = trace.merge(random_summary, on="round", how="left")
    final = merged.iloc[-1]
    improvement = float(final["best_so_far"] - final["random_mean"])
    if direction == "minimize":
        improvement = -improvement
    integrate = getattr(np, "trapezoid", np.trapz)
    bo_auc = float(integrate(merged["best_so_far"], merged["round"])) if len(merged) > 1 else float(merged["best_so_far"].iloc[0])
    random_auc = float(integrate(merged["random_mean"], merged["round"])) if len(merged) > 1 else float(merged["random_mean"].iloc[0])
    auc_improvement = bo_auc - random_auc if direction == "maximize" else random_auc - bo_auc
    return {
        "final_bo_best": float(final["best_so_far"]),
        "final_random_mean_best": float(final["random_mean"]),
        "final_random_p10": float(final["random_p10"]),
        "final_random_p90": float(final["random_p90"]),
        "improvement_over_random": improvement,
        "auc_improvement_over_random": float(auc_improvement),
        "n_rounds": int(len(trace)),
        "direction": direction,
        "beats_random_mean": bool(improvement > 0),
    }
