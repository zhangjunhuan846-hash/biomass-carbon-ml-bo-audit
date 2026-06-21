import pandas as pd
import pytest

from carbon_literature_bo_replay.features import make_xy, select_numeric_features, validate_requested_features


def test_target_like_feature_excluded():
    df = pd.DataFrame({"sample_id": ["a", "b"], "BET": [1, 2], "predicted_capacity": [3, 4], "ICE": [80, 90]})
    features, issues = select_numeric_features(df, "ICE", id_col="sample_id")
    assert "BET" in features
    assert "predicted_capacity" not in features
    assert issues


def test_validate_requested_features():
    df = pd.DataFrame({"BET": [1, 2, 3], "name": ["a", "b", "c"], "ICE": [80, 85, 90]})
    features, issues = validate_requested_features(df, ["BET", "missing", "name", "ICE"], "ICE")
    assert features == ["BET"]
    assert len(issues) == 3


def test_make_xy_requires_features():
    df = pd.DataFrame({"ICE": [80, 85, 90]})
    with pytest.raises(ValueError):
        make_xy(df, [], "ICE")
