from pathlib import Path
from carbon_literature_bo_replay.cli import main

ROOT = Path(__file__).resolve().parents[1]
main([
    "replay",
    "--data", str(ROOT / "examples" / "input" / "carbon_literature_demo.csv"),
    "--target", "ICE",
    "--id-col", "sample_id",
    "--paper-col", "paper_id",
    "--out", str(ROOT / "outputs" / "demo_replay"),
    "--seed-size", "8",
    "--iterations", "20",
    "--random-repeats", "20",
])
