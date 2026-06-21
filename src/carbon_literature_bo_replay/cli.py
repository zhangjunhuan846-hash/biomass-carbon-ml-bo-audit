from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .features import make_xy, select_numeric_features, validate_requested_features
from .io import read_table, write_json
from .leakage import audit_leakage
from .plotting import plot_replay
from .profile import profile_dataset
from .replay import (
    run_diversity_baseline,
    run_oracle_baseline,
    run_random_baseline,
    run_ucb_replay,
    summarize_replay,
)
from .report import write_report


def _parse_feature_list(raw: str) -> list[str]:
    return [f.strip() for f in raw.split(",") if f.strip()]


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

    features, feature_issues = select_numeric_features(
        df,
        args.target,
        args.id_col,
        args.paper_col,
        max_missing=args.max_missing,
    )
    if args.features:
        requested = _parse_feature_list(args.features)
        features, requested_issues = validate_requested_features(df, requested, args.target)
        feature_issues.extend(requested_issues)

    schema = {
        "selected_features": features,
        "excluded_or_flagged": feature_issues,
        "max_missing": args.max_missing,
        "selection_mode": "manual" if args.features else "automatic_conservative",
    }
    write_json(schema, state / "02_descriptor_schema.json")
    pd.DataFrame({"feature": features}).to_csv(out / "selected_features.csv", index=False)

    protocol = {
        "seed_size": args.seed_size,
        "iterations": args.iterations,
        "random_repeats": args.random_repeats,
        "acquisition": "ucb",
        "ucb_beta": args.beta,
        "direction": args.direction,
        "random_state": args.random_state,
    }
    write_json(protocol, state / "03_replay_protocol.json")

    clean, x, y = make_xy(df, features, args.target)
    trace, selected = run_ucb_replay(
        clean,
        x,
        y,
        seed_size=args.seed_size,
        iterations=args.iterations,
        beta=args.beta,
        random_state=args.random_state,
        direction=args.direction,
    )
    random_summary = run_random_baseline(
        y,
        seed_size=args.seed_size,
        iterations=args.iterations,
        repeats=args.random_repeats,
        random_state=args.random_state,
        direction=args.direction,
    )
    diversity = run_diversity_baseline(
        x,
        y,
        seed_size=args.seed_size,
        iterations=args.iterations,
        random_state=args.random_state,
        direction=args.direction,
    )
    exploit_trace, _ = run_ucb_replay(
        clean,
        x,
        y,
        seed_size=args.seed_size,
        iterations=args.iterations,
        beta=0.0,
        random_state=args.random_state,
        direction=args.direction,
    )
    exploit = exploit_trace[["round", "best_so_far"]].rename(columns={"best_so_far": "exploit_best"})
    oracle = run_oracle_baseline(
        y,
        seed_size=args.seed_size,
        iterations=args.iterations,
        random_state=args.random_state,
        direction=args.direction,
    )

    baseline_table = random_summary.merge(diversity[["round", "diversity_best"]], on="round", how="left")
    baseline_table = baseline_table.merge(exploit, on="round", how="left")
    baseline_table = baseline_table.merge(oracle[["round", "oracle_best"]], on="round", how="left")
    summary = summarize_replay(trace, random_summary, direction=args.direction)

    trace.to_csv(out / "replay_trace.csv", index=False)
    baseline_table.to_csv(out / "baseline_comparison.csv", index=False)
    write_json(
        {"rounds": trace.to_dict(orient="records"), "final_best": summary["final_bo_best"]},
        state / "05_acquisition_trace.json",
    )
    write_json(summary, state / "06_baseline_comparison.json")
    write_json(
        {
            "model": "RidgeSurrogate",
            "uncertainty": "distance_scaled_residual_proxy",
            "note": "Dependency-light surrogate; use GPR/RF only after enough complete samples are available.",
        },
        state / "04_surrogate_diagnostics.json",
    )

    rec = clean.iloc[selected].copy() if selected else clean.iloc[[]].copy()
    rec.insert(0, "selection_rank", range(1, len(rec) + 1))
    rec.to_csv(out / "recommended_candidates.csv", index=False)

    leakage_df, leakage_json = audit_leakage(df, args.target, features, args.paper_col)
    leakage_df.to_csv(out / "leakage_audit.csv", index=False)
    write_json(leakage_json, state / "07_leakage_audit.json")

    plot_replay(trace, baseline_table, figs / "bo_replay_curve.png")
    write_report(out / "bo_replay_report.md", profile, features, summary, leakage_json)
    print(f"Replay complete: {out}")
    print(f"Final BO best: {summary['final_bo_best']:.4g}")
    print(f"Final random mean best: {summary['final_random_mean_best']:.4g}")
    print(f"Decision report: {out / 'bo_replay_report.md'}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="carbon-bo-replay")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("replay", help="Run offline BO replay on a literature-derived materials dataset")
    r.add_argument("--data", required=True, help="Input CSV/TSV/XLSX file")
    r.add_argument("--target", required=True, help="Target column to optimize")
    r.add_argument("--id-col", default="sample_id", help="Sample identifier column")
    r.add_argument("--paper-col", default="paper_id", help="Paper/group identifier column for validity audit")
    r.add_argument(
        "--features",
        default="",
        help="Comma-separated numeric descriptor columns. If omitted, descriptors are auto-selected conservatively.",
    )
    r.add_argument("--out", default="outputs/bo_replay")
    r.add_argument("--seed-size", type=int, default=8)
    r.add_argument("--iterations", type=int, default=20)
    r.add_argument("--random-repeats", type=int, default=50)
    r.add_argument("--beta", type=float, default=0.5, help="UCB uncertainty weight")
    r.add_argument("--direction", choices=["maximize", "minimize"], default="maximize")
    r.add_argument("--max-missing", type=float, default=0.60, help="Maximum missing rate for automatic feature selection")
    r.add_argument("--random-state", type=int, default=42)
    r.set_defaults(func=run_replay)
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
