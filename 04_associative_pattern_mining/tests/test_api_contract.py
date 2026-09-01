import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from ml.pipeline import run_mining


def test_ml_adapter_returns_json_evidence_with_denominators():
    result = run_mining(0.25, 0.60, 6)
    assert result["transaction_count"] == 24
    assert result["minimum_support_count"] == 6
    assert len(result["itemsets"]) == 18
    assert len(result["rules"]) == 15
    assert result["rules"][0]["support_count"] == 6
    assert result["rules"][0]["antecedent_count"] > 0


def test_ml_adapter_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="min_support"):
        run_mining(0, 0.60, 1)
    with pytest.raises(ValueError, match="min_confidence"):
        run_mining(0.25, 0, 1)


def test_count_floor_can_only_make_prevalence_stricter():
    baseline = run_mining(0.25, 0.60, 1)
    strict = run_mining(0.25, 0.60, 12)
    assert strict["minimum_support_count"] == 12
    assert len(strict["itemsets"]) <= len(baseline["itemsets"])


def test_count_floor_rejects_impossible_denominator():
    with pytest.raises(ValueError, match="cannot exceed transaction count"):
        run_mining(0.25, 0.60, 25)
