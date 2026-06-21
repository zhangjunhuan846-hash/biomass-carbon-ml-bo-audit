from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from carbon_literature_bo_replay.cli import main

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
    "--direction", "maximize",
])
