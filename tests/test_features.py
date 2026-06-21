import pandas as pd
from carbon_literature_bo_replay.features import select_numeric_features


def test_target_like_feature_excluded():
    df = pd.DataFrame({"sample_id": ["a", "b"], "BET": [1, 2], "predicted_capacity": [3, 4], "ICE": [80, 90]})
    features, issues = select_numeric_features(df, "ICE", id_col="sample_id")
    assert "BET" in features
    assert "predicted_capacity" not in features
    assert issues
