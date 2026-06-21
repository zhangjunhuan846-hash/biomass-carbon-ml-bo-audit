from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from .io import read_table, write_json
from .profile import profile_dataset
from .features import select_numeric_features, make_xy
from .replay import run_ucb_replay, run_random_baseline, summarize_replay
from .leakage import audit_leakage
from .plotting import plot_replay
from .report import write_report


def run_replay(args: argparse.Namespace) -> None:
    out = Path(args.out)
    state = out / "state"
    figs = out / "figures"
    out.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    df = read_table(args.data)
    profile = profile_dataset(df, args.target, args.id_col, args.paper_col)
    write_json(profile, state / "01_dataset_profile.json")

    features, feature_issues = select_numeric_features(df, args.target, args.id_col, args.paper_col)
    if args.features:
        requested = [f.strip() for f in args.features.split(",") if f.strip()]
        features = [f for f in requested if f in df.columns and f != args.target]
    schema = {"selected_features": features, "excluded_or_flagged": feature_issues}
    write_json(schema, state / "02_descriptor_schema.json")
    pd.DataFrame({"feature": features}).to_csv(out / "selected_features.csv", index=False)

    protocol = {
        "seed_size": args.seed_size,
        "iterations": args.iterations,
        "random_repeats": args.random_repeats,
        "acquisition": "ucb",
        "ucb_beta": args.beta,
    }
    write_json(protocol, state / "03_replay_protocol.json")

    clean, x, y = make_xy(df, features, args.target)
    trace, selected = run_ucb_replay(clean, x, y, args.seed_size, args.iterations, args.beta, args.random_state)
    random_summary = run_random_baseline(y, args.seed_size, args.iterations, args.random_repeats, args.random_state)
    summary = summarize_replay(trace, random_summary)

    trace.to_csv(out / "replay_trace.csv", index=False)
    random_summary.to_csv(out / "baseline_comparison.csv", index=False)
    write_json({"rounds": trace.to_dict(orient="records"), "final_best": summary["final_bo_best"]}, state / "05_acquisition_trace.json")
    write_json(summary, state / "06_baseline_comparison.json")
    write_json({"model": "RidgeSurrogate", "uncertainty": "distance_scaled_residual_proxy"}, state / "04_surrogate_diagnostics.json")

    id_col = args.id_col if args.id_col in clean.columns else None
    rec = clean.iloc[selected].copy() if selected else clean.iloc[[]].copy()
    rec.insert(0, "selection_rank", range(1, len(rec) + 1))
    rec.to_csv(out / "recommended_candidates.csv", index=False)

    leakage_df, leakage_json = audit_leakage(df, args.target, features, args.paper_col)
    leakage_df.to_csv(out / "leakage_audit.csv", index=False)
    write_json(leakage_json, state / "07_leakage_audit.json")

    plot_replay(trace, random_summary, figs / "bo_replay_curve.png")
    write_report(out / "bo_replay_report.md", profile, features, summary, leakage_json)
    print(f"Replay complete: {out}")
    print(f"Final BO best: {summary['final_bo_best']:.4g}")
    print(f"Final random mean best: {summary['final_random_mean_best']:.4g}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="carbon-bo-replay")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("replay", help="Run offline BO replay on a literature dataset")
    r.add_argument("--data", required=True)
    r.add_argument("--target", required=True)
    r.add_argument("--id-col", default="sample_id")
    r.add_argument("--paper-col", default="paper_id")
    r.add_argument("--features", default="", help="Comma-separated feature columns. If omitted, numeric descriptors are auto-selected.")
    r.add_argument("--out", default="outputs/bo_replay")
    r.add_argument("--seed-size", type=int, default=8)
    r.add_argument("--iterations", type=int, default=20)
    r.add_argument("--random-repeats", type=int, default=50)
    r.add_argument("--beta", type=float, default=0.5)
    r.add_argument("--random-state", type=int, default=42)
    r.set_defaults(func=run_replay)
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
