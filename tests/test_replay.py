import numpy as np
import pandas as pd

from carbon_literature_bo_replay.replay import (
    run_diversity_baseline,
    run_oracle_baseline,
    run_random_baseline,
    run_ucb_replay,
    summarize_replay,
)


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
    assert "random_p90" in out.columns


def test_secondary_baselines_and_summary():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(25, 3))
    y = x[:, 0] - 0.2 * x[:, 1]
    data = pd.DataFrame(x)
    trace, _ = run_ucb_replay(data, x, y, seed_size=5, iterations=6)
    random = run_random_baseline(y, seed_size=5, iterations=6, repeats=5)
    diversity = run_diversity_baseline(x, y, seed_size=5, iterations=6)
    oracle = run_oracle_baseline(y, seed_size=5, iterations=6)
    summary = summarize_replay(trace, random)
    assert len(diversity) == 6
    assert len(oracle) == 6
    assert summary["n_rounds"] == 6
    assert "auc_improvement_over_random" in summary


def test_minimize_direction():
    rng = np.random.default_rng(2)
    x = rng.normal(size=(20, 2))
    y = np.linspace(10, 1, 20)
    data = pd.DataFrame(x)
    trace, _ = run_ucb_replay(data, x, y, seed_size=4, iterations=5, direction="minimize")
    assert trace["best_so_far"].iloc[-1] <= trace["best_so_far"].iloc[0]
