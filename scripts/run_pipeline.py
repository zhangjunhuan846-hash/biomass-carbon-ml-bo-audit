from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full audit + offline BO replay pipeline.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", default="ice_percent")
    parser.add_argument("--outdir", default="outputs/pipeline")
    parser.add_argument("--n-init", type=int, default=8)
    parser.add_argument("--budget", type=int, default=15)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--beta", type=float, default=1.0)
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    audit_out = outdir
    run([sys.executable, "scripts/audit_dataset.py", "--input", args.input, "--target", args.target, "--outdir", str(audit_out)])
    modeling_ready = audit_out / "modeling_ready.csv"
    run([
        sys.executable, "scripts/run_offline_bo_replay.py",
        "--input", str(modeling_ready), "--target", args.target, "--outdir", str(outdir),
        "--n-init", str(args.n_init), "--budget", str(args.budget), "--seeds", str(args.seeds), "--beta", str(args.beta)
    ])
    print(f"\nPipeline complete. Open: {outdir / 'audit_report.md'} and {outdir / 'bo_replay_summary.md'}")


if __name__ == "__main__":
    main()
