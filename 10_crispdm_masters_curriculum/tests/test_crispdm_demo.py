import json

from src.crispdm_demo import build_model, load_iris, prepare_data, run


def test_split_is_stratified_and_reproducible():
    data = load_iris()
    first = prepare_data(data)
    second = prepare_data(data)
    assert [part.tolist() for part in first] == [part.tolist() for part in second]
    assert len(first[0]) == 120 and len(first[1]) == 30


def test_model_meets_success_criterion(tmp_path):
    report = run(tmp_path)
    assert report["evaluation"]["accuracy"] >= 0.90
    assert (tmp_path / "crispdm_report.json").exists()
    assert (tmp_path / "iris_snapshot.csv").exists()


def test_report_contains_all_crispdm_phases(tmp_path):
    run(tmp_path)
    report = json.loads((tmp_path / "crispdm_report.json").read_text())
    assert set(report) == {
        "business_understanding", "data_understanding", "data_preparation",
        "modeling", "evaluation", "deployment",
    }
    assert build_model().steps[-1][0] == "classifier"
