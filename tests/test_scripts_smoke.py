from pathlib import Path
import subprocess
import sys


def test_pipeline_smoke(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    data = repo / "examples" / "sib_hard_carbon_synthetic" / "synthetic_sib_hard_carbon.csv"
    out = tmp_path / "smoke"
    subprocess.run([
        sys.executable, str(repo / "scripts" / "run_pipeline.py"),
        "--input", str(data),
        "--target", "ice_percent",
        "--outdir", str(out),
        "--n-init", "6",
        "--budget", "8",
        "--seeds", "3",
    ], check=True, cwd=repo)
    assert (out / "audit_report.md").exists()
    assert (out / "bo_replay_summary.md").exists()
    assert (out / "bo_replay_curve.png").exists()
