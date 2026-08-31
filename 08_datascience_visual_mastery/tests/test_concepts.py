import math

import pytest

from src.concepts import (backprop_demo, gradient_descent, naive_bayes_posterior,
                          quadratic, quadratic_derivative, threshold_metrics)
from src.generate_plots import save_figures


def test_bayes_matches_hand_calculation_and_monotonicity():
    assert naive_bayes_posterior(0.5, 0.8, 0.2) == pytest.approx(0.8)
    values = [naive_bayes_posterior(p, 0.8, 0.2) for p in (0.1, 0.5, 0.9)]
    assert values == sorted(values)


def test_threshold_metrics_and_costs():
    result = threshold_metrics([1, 1, 0, 0], [0.9, 0.3, 0.8, 0.1], 0.5)
    assert (result.tp, result.fp, result.tn, result.fn) == (1, 1, 1, 1)
    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)
    assert result.cost == 5


def test_gradient_descent_reduces_loss_and_derivative_is_zero_at_minimum():
    path = gradient_descent()
    assert quadratic_derivative(3) == 0
    assert quadratic(path[-1]) < quadratic(path[0])
    assert all(math.isfinite(value) for value in path)


def test_chain_rule_product_is_consistent():
    values = backprop_demo()
    assert values["dL_dw"] == pytest.approx(values["dL_dy"] * values["dy_dw"])
    assert values["dL_db"] == pytest.approx(values["dL_dy"] * values["dy_db"])


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
