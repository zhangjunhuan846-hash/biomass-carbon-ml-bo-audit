import pandas as pd
from carbon_literature_bo_replay.profile import profile_dataset


def test_profile_dataset():
    df = pd.DataFrame({"sample_id": ["a", "b"], "paper_id": ["p1", "p2"], "BET": [100, 200], "ICE": [80, 85]})
    p = profile_dataset(df, "ICE", "sample_id", "paper_id")
    assert p["n_rows"] == 2
    assert p["target"] == "ICE"
    assert "BET" in p["numeric_features"]
