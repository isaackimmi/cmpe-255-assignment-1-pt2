import json
import sys
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from analysis import apriori, association_rules, load_transaction_rows, load_transactions, support

ROOT = Path(__file__).parents[1]


def brute_force(transactions, min_support):
    universe = sorted(set().union(*transactions))
    return {
        frozenset(items): support(frozenset(items), transactions)
        for size in range(1, len(universe) + 1)
        for items in combinations(universe, size)
        if support(frozenset(items), transactions) >= min_support
    }


def test_dataset_is_deterministic_and_nonempty():
    transactions = load_transactions()
    assert len(transactions) == 24
    assert transactions[0] == {"bread", "milk", "eggs"}


def test_apriori_prunes_and_calculates_support():
    frequent = apriori(load_transactions(), min_support=0.25)
    assert frequent[frozenset({"bread"})] == 19 / 24
    assert frequent[frozenset({"bread", "milk"})] == 13 / 24
    assert frozenset({"bread", "jam", "eggs"}) not in frequent


def test_apriori_matches_independent_brute_force_oracle():
    transactions = load_transactions()
    for minimum in (0.10, 0.25, 0.30, 0.50, 0.70):
        assert apriori(transactions, minimum) == brute_force(transactions, minimum)


def test_rules_include_metrics_and_improvement_filter():
    rules = association_rules(apriori(load_transactions()), min_confidence=0.60)
    assert rules
    assert all(0 < r["support"] <= 1 and 0 < r["confidence"] <= 1 and r["lift"] > 0 for r in rules)
    assert any(r["lift"] > 1 for r in rules)


def test_rule_metrics_use_exact_support_denominators():
    rules = association_rules(apriori(load_transactions(), min_support=0.25), min_confidence=0.60)
    rule = next(r for r in rules if r["antecedent"] == {"bread", "jam"} and r["consequent"] == {"butter"})
    assert rule["support"] == pytest.approx(6 / 24)
    assert rule["confidence"] == pytest.approx(1.0)
    assert rule["lift"] == pytest.approx(24 / 13)


def test_threshold_and_metric_validation():
    transactions = load_transactions()
    with pytest.raises(ValueError, match="min_support"):
        apriori(transactions, 0)
    with pytest.raises(ValueError, match="min_support"):
        apriori(transactions, 1.01)
    with pytest.raises(ValueError, match="min_confidence"):
        association_rules(apriori(transactions), 0)
    with pytest.raises(ValueError, match="itemset"):
        support(frozenset(), transactions)
    with pytest.raises(ValueError, match="non-empty"):
        support(frozenset({"bread"}), [])
    with pytest.raises(ValueError, match="missing"):
        association_rules({frozenset({"bread", "milk"}): 0.5}, 0.6)


def test_loader_trims_items_and_documents_duplicate_policy(tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text('transaction_id,items\nT1," bread ; milk ; bread "\n', encoding="utf-8")
    assert load_transaction_rows(path) == [{"transaction_id": "T1", "items": frozenset({"bread", "milk"})}]


@pytest.mark.parametrize(
    "contents, message",
    [
        ("transaction_id,items\nT1,\n", "no products"),
        ('transaction_id,items\nT1,"bread;;milk"\n', "empty product token"),
        ('transaction_id,items\nT1,bread\nT1,milk\n', "repeats"),
        ('transaction_id,items\nT1,bread,unexpected\n', "extra CSV fields"),
        ("transaction_id\nT1\n", "exactly these columns"),
    ],
)
def test_loader_rejects_malformed_rows(tmp_path, contents, message):
    path = tmp_path / "bad.csv"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_transaction_rows(path)


def test_browser_data_is_generated_from_the_same_csv():
    generated = ROOT / "data" / "transactions.js"
    payload = generated.read_text(encoding="utf-8").split(" = ", 1)[1].removesuffix(";\n")
    browser_rows = json.loads(payload)
    python_rows = [
        {"id": row["transaction_id"], "items": sorted(row["items"])}
        for row in load_transaction_rows()
    ]
    assert browser_rows == python_rows
