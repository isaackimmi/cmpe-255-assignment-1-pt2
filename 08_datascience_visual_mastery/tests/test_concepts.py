import math

import pytest

from src.concepts import (backprop_demo, gradient_descent, naive_bayes_posterior,
                          quadratic, quadratic_derivative, roc_auc, roc_points,
                          sigmoid, threshold_metrics)
from src.generate_plots import save_figures


def test_bayes_matches_hand_calculation_and_monotonicity():
    assert naive_bayes_posterior(0.5, 0.8, 0.2) == pytest.approx(0.8)
    assert naive_bayes_posterior(0.5, [0.8, 0.7], [0.2, 0.3]) == pytest.approx(0.9032258)
    values = [naive_bayes_posterior(p, 0.8, 0.2) for p in (0.1, 0.5, 0.9)]
    assert values == sorted(values)


def test_bayes_rejects_impossible_evidence_and_accepts_prior_endpoints():
    with pytest.raises(ValueError, match="zero probability"):
        naive_bayes_posterior(0.5, 0.0, 0.0)
    assert naive_bayes_posterior(0.0, 0.8, 0.2) == 0
    assert naive_bayes_posterior(1.0, 0.8, 0.2) == 1


def test_threshold_metrics_and_costs():
    result = threshold_metrics([1, 1, 0, 0], [0.9, 0.3, 0.8, 0.1], 0.5)
    assert (result.tp, result.fp, result.tn, result.fn) == (1, 1, 1, 1)
    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)
    assert result.cost == 5
    assert result.cost_matrix.false_negative == 4


def test_threshold_metrics_validates_inputs_and_marks_undefined_ratios():
    assert threshold_metrics([0, 0], [0.1, 0.2], 0.5).precision is None
    assert threshold_metrics([1, 1], [0.1, 0.2], 0.5).fpr is None
    assert threshold_metrics([0, 0], [0.1, 0.2], 0.5, zero_division="zero").precision == 0
    for labels, scores in [([2, 0], [0.9, 0.1]), ([0, 1], [math.nan, 0.2]), ([0, 1], [0.2, 1.1])]:
        with pytest.raises(ValueError):
            threshold_metrics(labels, scores, 0.5)
    with pytest.raises(ValueError):
        threshold_metrics([0, 1], [0.2, 0.8], 0.5, false_negative_cost=-1)


def test_roc_points_include_endpoints_and_auc_is_ranking_area():
    labels = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    scores = [.95, .83, .62, .36, .79, .55, .41, .18, .09, .02]
    points = roc_points(labels, scores)
    assert points[0][:2] == (0.0, 0.0)
    assert points[-1][:2] == (1.0, 1.0)
    assert roc_auc(labels, scores) == pytest.approx(5 / 6)


def test_gradient_descent_reduces_loss_and_derivative_is_zero_at_minimum():
    path = gradient_descent()
    assert quadratic_derivative(3) == 0
    assert quadratic(path[-1]) < quadratic(path[0])
    assert all(math.isfinite(value) for value in path)


def test_chain_rule_product_is_consistent():
    values = backprop_demo()
    assert values["dL_dw"] == pytest.approx(values["dL_dy"] * values["dy_dw"])
    assert values["dL_db"] == pytest.approx(values["dL_dy"] * values["dy_db"])
    assert values["dy_dwx"] == 1
    assert values["dwx_dw"] == 2


def test_sigmoid_is_stable_for_large_finite_inputs():
    assert sigmoid(-1000) == pytest.approx(0.0)
    assert sigmoid(1000) == pytest.approx(1.0)
    assert sigmoid(-1000) < sigmoid(0) < sigmoid(1000)
    assert all(math.isfinite(sigmoid(value)) for value in (-1000, 0, 1000))


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError): naive_bayes_posterior(1.2, 0.5, 0.5)
    with pytest.raises(ValueError): threshold_metrics([], [], 0.5)
    with pytest.raises(ValueError): gradient_descent(steps=-1)


def test_plot_manifest_is_created(tmp_path, monkeypatch):
    import src.generate_plots as plots
    monkeypatch.setattr(plots, "OUT", tmp_path)
    manifest = save_figures()
    assert set(manifest) in ({"naive_bayes.png", "evaluation.png", "gradient_descent.png", "backpropagation.png"},
                             {"naive_bayes.svg", "evaluation.svg", "gradient_descent.svg", "backpropagation.svg"})
    assert all((tmp_path / filename).exists() for filename in manifest)


def test_dependency_free_artifacts_describe_each_concept(tmp_path, monkeypatch):
    import src.generate_plots as plots
    monkeypatch.setattr(plots, "OUT", tmp_path)
    monkeypatch.setattr(plots, "np", None)
    monkeypatch.setattr(plots, "plt", None)
    manifest = save_figures()
    contents = {name: (tmp_path / name).read_text() for name in manifest}
    assert "feature₁" in contents["naive_bayes.svg"]
    assert "ROC-AUC" in contents["evaluation.svg"]
    assert "Cost matrix" in contents["evaluation.svg"]
    assert "f′(x)" in contents["gradient_descent.svg"]
    assert "w×x" in contents["backpropagation.svg"]
    assert "generated snapshot" not in "".join(contents.values())
