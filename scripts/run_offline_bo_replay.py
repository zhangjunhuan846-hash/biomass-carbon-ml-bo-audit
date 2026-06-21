from __future__ import annotations

import argparse
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from utils import read_table, numeric_features, DEFAULT_FEATURES, boolish_yes, write_markdown_table

warnings.filterwarnings("ignore", category=UserWarning)


def prepare_xy(df: pd.DataFrame, target: str, features: list[str] | None = None, strict_quality: bool = False):
    data = df.copy()
    if strict_quality and "quality_tier" in data.columns:
        data = data[~data["quality_tier"].isin(["Tier2", "Tier3"])]
    data = data[data[target].notna()].copy()
    feats = numeric_features(data, features or DEFAULT_FEATURES)
    if not feats:
        raise ValueError("No numeric feature columns available for modeling.")
    X = data[feats].copy()
    y = pd.to_numeric(data[target], errors="coerce")
    valid = y.notna()
    return data.loc[valid].reset_index(drop=True), X.loc[valid].reset_index(drop=True), y.loc[valid].reset_index(drop=True), feats


def evaluate_baselines(data: pd.DataFrame, X: pd.DataFrame, y: pd.Series, outdir: Path) -> pd.DataFrame:
    rows = []
    if len(y) < 10:
        return pd.DataFrame([{"split":"none", "model":"not_run", "note":"fewer than 10 target values"}])

    def add_metrics(split_name, model_name, y_true, pred):
        rmse = float(np.sqrt(mean_squared_error(y_true, pred)))
        mae = float(mean_absolute_error(y_true, pred))
        r2 = float(r2_score(y_true, pred)) if len(set(y_true)) > 1 else np.nan
        rows.append({"split": split_name, "model": model_name, "n_test": len(y_true), "rmse": rmse, "mae": mae, "r2": r2})

    # Random split
    test_size = 0.25 if len(y) >= 40 else 0.3
    idx_train, idx_test = train_test_split(np.arange(len(y)), test_size=test_size, random_state=42)
    median = float(np.median(y.iloc[idx_train]))
    add_metrics("random", "median", y.iloc[idx_test], np.full(len(idx_test), median))
    models = {
        "extra_trees": ExtraTreesRegressor(n_estimators=120, random_state=42, min_samples_leaf=2),
        "random_forest": RandomForestRegressor(n_estimators=160, random_state=42, min_samples_leaf=2),
        "gradient_boosting": GradientBoostingRegressor(random_state=42),
    }
    for name, model in models.items():
        pipe = make_pipeline(SimpleImputer(strategy="median"), model)
        pipe.fit(X.iloc[idx_train], y.iloc[idx_train])
        pred = pipe.predict(X.iloc[idx_test])
        add_metrics("random", name, y.iloc[idx_test], pred)

    # Paper group split
    if "paper_id" in data.columns and data["paper_id"].nunique(dropna=True) >= 4:
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=7)
        groups = data["paper_id"].astype(str)
        tr, te = next(gss.split(X, y, groups=groups))
        median = float(np.median(y.iloc[tr]))
        add_metrics("paper_group", "median", y.iloc[te], np.full(len(te), median))
        for name, model in models.items():
            pipe = make_pipeline(SimpleImputer(strategy="median"), model)
            pipe.fit(X.iloc[tr], y.iloc[tr])
            pred = pipe.predict(X.iloc[te])
            add_metrics("paper_group", name, y.iloc[te], pred)

    # Time split
    if "year" in data.columns and data["year"].notna().sum() >= 10 and data["year"].nunique() >= 4:
        ordered = data.sort_values("year").index.to_numpy()
        cut = int(0.75 * len(ordered))
        tr, te = ordered[:cut], ordered[cut:]
        if len(te) >= 3:
            median = float(np.median(y.iloc[tr]))
            add_metrics("time", "median", y.iloc[te], np.full(len(te), median))
            for name, model in models.items():
                pipe = make_pipeline(SimpleImputer(strategy="median"), model)
                pipe.fit(X.iloc[tr], y.iloc[tr])
                pred = pipe.predict(X.iloc[te])
                add_metrics("time", name, y.iloc[te], pred)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(outdir / "model_metrics.csv", index=False)
    return metrics


def predict_with_uncertainty(model: ExtraTreesRegressor, X_pool: np.ndarray):
    preds = np.vstack([tree.predict(X_pool) for tree in model.estimators_])
    return preds.mean(axis=0), preds.std(axis=0)


def bo_replay_once(X: pd.DataFrame, y: pd.Series, seed: int, n_init: int, budget: int, beta: float):
    rng = np.random.default_rng(seed)
    n = len(y)
    if n_init >= n:
        raise ValueError("n_init must be smaller than dataset size.")
    all_idx = np.arange(n)
    observed = list(rng.choice(all_idx, size=n_init, replace=False))
    available = [i for i in all_idx if i not in observed]
    best_so_far = [float(np.max(y.iloc[observed]))]
    selected_order = []

    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(X)

    steps = min(budget, len(available))
    for _ in range(steps):
        model = ExtraTreesRegressor(n_estimators=120, random_state=seed, min_samples_leaf=2, bootstrap=True)
        model.fit(X_imp[observed], y.iloc[observed])
        mu, sigma = predict_with_uncertainty(model, X_imp[available])
        acquisition = mu + beta * sigma
        chosen_pos = int(np.argmax(acquisition))
        chosen = available.pop(chosen_pos)
        observed.append(chosen)
        selected_order.append(chosen)
        best_so_far.append(float(max(best_so_far[-1], y.iloc[chosen])))
    return best_so_far, selected_order


def random_replay_once(y: pd.Series, seed: int, n_init: int, budget: int):
    rng = np.random.default_rng(seed + 10_000)
    n = len(y)
    order = list(rng.permutation(np.arange(n)))
    observed = order[:n_init]
    rest = order[n_init:n_init+budget]
    best = [float(np.max(y.iloc[observed]))]
    for idx in rest:
        best.append(float(max(best[-1], y.iloc[idx])))
    return best, rest


def run_replays(data: pd.DataFrame, X: pd.DataFrame, y: pd.Series, seeds: int, n_init: int, budget: int, beta: float, outdir: Path):
    bo_rows, random_rows = [], []
    candidate_counter = {}
    for seed in range(seeds):
        bo_curve, bo_selected = bo_replay_once(X, y, seed, n_init, budget, beta)
        rnd_curve, rnd_selected = random_replay_once(y, seed, n_init, budget)
        for step, val in enumerate(bo_curve):
            bo_rows.append({"method":"model_ucb", "seed":seed, "step":step, "best_so_far":val})
        for step, val in enumerate(rnd_curve):
            random_rows.append({"method":"random", "seed":seed, "step":step, "best_so_far":val})
        for rank, idx in enumerate(bo_selected[:10], start=1):
            candidate_counter[idx] = candidate_counter.get(idx, 0) + (11-rank)
    curves = pd.DataFrame(bo_rows + random_rows)
    curves.to_csv(outdir / "bo_replay_curves.csv", index=False)

    # top candidates across seeds
    top_indices = sorted(candidate_counter, key=candidate_counter.get, reverse=True)[:30]
    cols = [c for c in ["sample_id", "paper_id", "year", "device_system", "precursor", "quality_tier", "needs_manual_check", "check_reason", "doi", "source_location"] if c in data.columns]
    top_candidates = data.loc[top_indices, cols].copy()
    top_candidates["target_value"] = y.iloc[top_indices].values
    top_candidates["selection_score"] = [candidate_counter[i] for i in top_indices]
    top_candidates = top_candidates.sort_values(["selection_score", "target_value"], ascending=False)
    top_candidates.to_csv(outdir / "top_candidate_queue.csv", index=False)

    # plot
    summary = curves.groupby(["method", "step"])["best_so_far"].agg(["mean", "std"]).reset_index()
    plt.figure(figsize=(7, 4.5))
    for method, sub in summary.groupby("method"):
        plt.plot(sub["step"], sub["mean"], label=method)
        plt.fill_between(sub["step"], sub["mean"]-sub["std"], sub["mean"]+sub["std"], alpha=0.15)
    plt.xlabel("Replay step")
    plt.ylabel("Best target so far")
    plt.title("Offline BO replay vs random search")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "bo_replay_curve.png", dpi=200)
    plt.close()

    final = curves.groupby(["method", "seed"]).tail(1).groupby("method")["best_so_far"].agg(["mean", "std", "min", "max"]).reset_index()
    final.to_csv(outdir / "bo_replay_final_summary.csv", index=False)
    return curves, final, top_candidates


def write_replay_report(metrics: pd.DataFrame, final: pd.DataFrame, top_candidates: pd.DataFrame, target: str, features: list[str], outdir: Path):
    report = [f"# Offline BO replay summary\n", f"Target: `{target}`\n", f"Features used: `{', '.join(features)}`\n"]
    report.append("## Baseline model metrics\n")
    report.append(write_markdown_table(metrics, max_rows=30))
    report.append("\n## Replay final best-so-far summary\n")
    report.append(write_markdown_table(final, max_rows=10))
    report.append("\n## Top historical candidates prioritized by replay\n")
    report.append(write_markdown_table(top_candidates.head(20), max_rows=20))
    report.append("\n## Interpretation\n")
    if set(final["method"]) >= {"model_ucb", "random"}:
        m = final.set_index("method")
        gain = float(m.loc["model_ucb", "mean"] - m.loc["random", "mean"])
        report.append(f"Mean final best-so-far gain over random: **{gain:.3g} target units**.\n")
        if gain > 0:
            report.append("The replay suggests possible prioritization value, but this remains an offline historical test. Check whether top candidates are source-verified and not dominated by one paper.\n")
        else:
            report.append("The replay does not show a clear advantage over random search under this configuration. Prioritize curation, feature quality, or target/protocol filtering before stronger claims.\n")
    report.append("\nDo not describe these as new material discoveries. They are historical candidates prioritized by offline replay.\n")
    (outdir / "bo_replay_summary.md").write_text("\n".join(report), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run ML baselines and offline BO replay on a literature dataset.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", default="ice_percent")
    parser.add_argument("--outdir", default="outputs/bo_replay")
    parser.add_argument("--n-init", type=int, default=8)
    parser.add_argument("--budget", type=int, default=15)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--strict-quality", action="store_true", help="Exclude Tier2/Tier3 before modeling")
    parser.add_argument("--features", nargs="*", default=None)
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df = read_table(args.input)
    if args.target not in df.columns:
        raise ValueError(f"Target `{args.target}` not found. Available columns: {list(df.columns)}")
    data, X, y, feats = prepare_xy(df, args.target, args.features, strict_quality=args.strict_quality)
    if len(y) < max(args.n_init + 3, 15):
        raise ValueError(f"Need at least {max(args.n_init + 3, 15)} target values for replay; found {len(y)}.")
    metrics = evaluate_baselines(data, X, y, outdir)
    curves, final, top_candidates = run_replays(data, X, y, seeds=args.seeds, n_init=args.n_init, budget=args.budget, beta=args.beta, outdir=outdir)
    write_replay_report(metrics, final, top_candidates, args.target, feats, outdir)
    print(f"Replay complete: {outdir}")


if __name__ == "__main__":
    main()
