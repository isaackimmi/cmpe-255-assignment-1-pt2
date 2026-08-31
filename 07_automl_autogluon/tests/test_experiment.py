import json

import pandas as pd

from src.experiment import SEED, load_data, run_experiment, split_data


def test_dataset_and_split_are_reproducible():
    X, y = load_data()
    first = split_data(X, y)
    second = split_data(X, y)
    assert X.shape == (569, 30)
    assert y.nunique() == 2
    assert first[0].equals(second[0])
    assert first[3].equals(second[3])


def test_sklearn_fallback_writes_ranked_metrics(tmp_path):
    leaderboard = run_experiment(tmp_path, include_autogluon=False)
    assert isinstance(leaderboard, pd.DataFrame)
    assert len(leaderboard) == 4
    assert leaderboard["rank"].tolist() == [1, 2, 3, 4]
    assert leaderboard["roc_auc"].between(0.5, 1.0).all()
    assert leaderboard["backend"].eq("sklearn").all()
    assert (tmp_path / "leaderboard.csv").exists()
    metadata = json.loads((tmp_path / "metrics.json").read_text())
    assert metadata["backend"] == "sklearn_fallback"
    assert metadata["random_seed"] == SEED
