import json
import hashlib
from pathlib import Path

import joblib
import pytest

from src.crispdm_demo import build_model, load_iris, prepare_data, run, split_indices
from src.inference import load_model_bundle, predict, predict_named, validate_features, validate_named_features


def test_split_is_stratified_and_reproducible():
    data = load_iris()
    first = prepare_data(data)
    second = prepare_data(data)
    assert [part.tolist() for part in first] == [part.tolist() for part in second]
    assert len(first[0]) == 120 and len(first[1]) == 30


def test_report_records_baseline_uncertainty_and_reproducibility(tmp_path):
    report = run(tmp_path)
    evaluation = report["evaluation"]
    assert evaluation["correct"] + len(evaluation["failure_cases"]) == evaluation["total"]
    assert len(evaluation["accuracy_95_wilson_interval"]) == 2
    assert evaluation["majority_baseline"]["accuracy_delta"] > 0
    assert report["modeling"]["selection_protocol"] == "3 repeats of 5-fold stratified CV on training rows only"
    assert report["modeling"]["beats_baseline_in_cv"] is True
    assert report["modeling"]["selected_cv_accuracy"] > report["modeling"]["baseline_cv_accuracy"]
    assert report["runtime"]["scikit_learn"]
    assert report["data_understanding"]["content_sha256"]
    assert (tmp_path / "crispdm_report.json").exists()
    assert (tmp_path / "iris_snapshot.csv").exists()
    assert (tmp_path / "model.joblib").exists()
    assert report["artifacts"]["iris_snapshot.csv"]["sha256"] == hashlib.sha256((tmp_path / "iris_snapshot.csv").read_bytes()).hexdigest()
    assert report["artifacts"]["model.joblib"]["sha256"] == hashlib.sha256((tmp_path / "model.joblib").read_bytes()).hexdigest()
    assert len(evaluation["holdout_cases"]) == evaluation["total"]
    assert all(set(case["features"]) == set(report["data_understanding"]["features"]) for case in evaluation["holdout_cases"])
    assert report["deployment"]["validation_semantics"]["success_gate"].startswith("Pass only when modeling.beats_baseline_in_cv")
    assert report["modeling"]["model_configuration_fingerprint"] != report["modeling"]["fitted_model_fingerprint"]


def test_report_contains_all_crispdm_phases(tmp_path):
    run(tmp_path)
    report = json.loads((tmp_path / "crispdm_report.json").read_text())
    assert {
        "business_understanding", "data_understanding", "data_preparation",
        "modeling", "evaluation", "deployment", "artifacts", "runtime",
    }.issubset(report)
    assert report["data_preparation"]["train_test_overlap_rows"] == 0
    assert report["data_understanding"]["quality_checks"]["schema_valid"] is True
    assert build_model().steps[-1][0] == "classifier"


def test_split_indices_are_disjoint_and_stratified():
    data = load_iris()
    train, test = split_indices(data)
    assert set(train).isdisjoint(test)
    assert sorted((data.target[test] == label).sum() for label in range(3)) == [10, 10, 10]


def test_inference_enforces_contract_and_returns_prediction(tmp_path):
    run(tmp_path)
    prediction = predict(tmp_path / "model.joblib", [5.1, 3.5, 1.4, 0.2])
    assert prediction["predicted_class"] == "setosa"
    assert len(prediction["probabilities"]) == 3
    with pytest.raises(ValueError, match="exactly 4"):
        validate_features([5.1, 3.5], report_contract(tmp_path))
    with pytest.raises(ValueError, match="inclusive range"):
        validate_features([5.1, 3.5, 1.4, 11.0], report_contract(tmp_path))
    named = {
        "petal width (cm)": 0.2,
        "sepal length (cm)": 5.1,
        "petal length (cm)": 1.4,
        "sepal width (cm)": 3.5,
    }
    assert validate_named_features(named, report_contract(tmp_path)).tolist() == [[5.1, 3.5, 1.4, 0.2]]
    assert predict_named(tmp_path / "model.joblib", named)["predicted_class"] == "setosa"
    with pytest.raises(ValueError, match="missing=.*extra"):
        validate_named_features({**named, "unexpected (cm)": 1.0}, report_contract(tmp_path))
    with pytest.raises(ValueError, match="missing=.*extra"):
        validate_named_features({key: value for key, value in named.items() if key != "petal width (cm)"}, report_contract(tmp_path))
    with pytest.raises(ValueError, match="finite numeric"):
        validate_features([5.1, "not-a-number", 1.4, 0.2], report_contract(tmp_path))
    with pytest.raises(ValueError, match="finite numeric"):
        validate_features([5.1, 3.5, float("nan"), 0.2], report_contract(tmp_path))
    wrong_units = {**report_contract(tmp_path), "units": "mm"}
    with pytest.raises(ValueError, match="units"):
        validate_features([5.1, 3.5, 1.4, 0.2], wrong_units)


def test_bundle_loader_rejects_incompatible_schema_and_fingerprint(tmp_path):
    run(tmp_path)
    bundle = joblib.load(tmp_path / "model.joblib")
    bundle["bundle_schema_version"] = "1.0"
    incompatible_path = tmp_path / "incompatible.joblib"
    joblib.dump(bundle, incompatible_path)
    with pytest.raises(ValueError, match="Unsupported model bundle schema"):
        load_model_bundle(incompatible_path)

    bundle = joblib.load(tmp_path / "model.joblib")
    bundle["fitted_model_fingerprint"] = "0" * 64
    joblib.dump(bundle, incompatible_path)
    with pytest.raises(ValueError, match="fitted-artifact fingerprint"):
        load_model_bundle(incompatible_path)

    bundle = joblib.load(tmp_path / "model.joblib")
    (tmp_path / "iris_snapshot.csv").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="snapshot hash"):
        load_model_bundle(tmp_path / "model.joblib")


def test_run_is_byte_reproducible(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    run(first_dir)
    run(second_dir)
    for filename in ("crispdm_report.json", "iris_snapshot.csv", "model.joblib"):
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()


def report_contract(tmp_path):
    return json.loads((tmp_path / "crispdm_report.json").read_text())["deployment"]["input_contract"]


def test_dashboard_exposes_artifact_explorer_and_uses_cv_gate():
    source = Path(__file__).parents[1].joinpath("src", "app.js").read_text()
    html = Path(__file__).parents[1].joinpath("index.html").read_text()
    assert "report.modeling.beats_baseline_in_cv" in source
    assert "baseline.accuracy_delta > 0" not in source
    for control in ("model-select", "baseline-select", "metric-select", "inference-form"):
        assert control in html
    assert "data-matrix-row" in source and "holdout_cases" in source
