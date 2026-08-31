import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from analysis import apriori, association_rules, load_transactions

def test_dataset_is_deterministic_and_nonempty():
    transactions = load_transactions()
    assert len(transactions) == 24
    assert transactions[0] == {"bread", "milk", "eggs"}

def test_apriori_prunes_and_calculates_support():
    frequent = apriori(load_transactions(), min_support=0.25)
    assert frequent[frozenset({"bread"})] == 19 / 24
    assert frequent[frozenset({"bread", "milk"})] == 13 / 24
    assert frozenset({"bread", "jam", "eggs"}) not in frequent

def test_rules_include_metrics_and_improvement_filter():
    rules = association_rules(apriori(load_transactions()), min_confidence=0.60)
    assert rules
    assert all(0 < r["support"] <= 1 and 0 < r["confidence"] <= 1 and r["lift"] > 0 for r in rules)
    assert any(r["lift"] > 1 for r in rules)
