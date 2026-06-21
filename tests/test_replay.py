import numpy as np
import pandas as pd
from carbon_literature_bo_replay.replay import run_ucb_replay, run_random_baseline


def test_replay_outputs_rounds():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(30, 4))
    y = x[:, 0] * 2 + rng.normal(size=30)
    data = pd.DataFrame(x, columns=list("abcd"))
    trace, selected = run_ucb_replay(data, x, y, seed_size=5, iterations=7)
    assert len(trace) == 7
    assert len(selected) == 7
    assert "best_so_far" in trace.columns


def test_random_baseline_outputs():
    y = np.arange(20.0)
    out = run_random_baseline(y, seed_size=3, iterations=5, repeats=4)
    assert len(out) == 5
    assert "random_mean" in out.columns
