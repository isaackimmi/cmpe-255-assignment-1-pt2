"""Threshold validation and canonical Apriori orchestration."""
from __future__ import annotations

from pathlib import Path

from analysis import association_rules, apriori, minimum_support_count, support_count
from .repository import transaction_sets
from .serialization import serialize_itemsets, serialize_rules


def _validate_count(min_count: int, transaction_count: int) -> None:
    if not isinstance(min_count, int) or isinstance(min_count, bool) or min_count < 1:
        raise ValueError("min_count must be a positive integer")
    if min_count > transaction_count:
        raise ValueError(f"min_count cannot exceed transaction count ({transaction_count})")


def run_mining(min_support: float = 0.25, min_confidence: float = 0.60, min_count: int = 1) -> dict:
    transactions = transaction_sets()
    _validate_count(min_count, len(transactions))
    frequent = apriori(transactions, min_support=min_support)
    threshold_count = max(minimum_support_count(min_support, len(transactions)), min_count)
    frequent = {
        items: support
        for items, support in frequent.items()
        if support_count(items, transactions) >= threshold_count
    }
    rules = association_rules(frequent, min_confidence=min_confidence)
    itemsets = serialize_itemsets(frequent, transactions)
    serialized_rules = serialize_rules(rules, transactions)
    return {
        "data_source": str(Path("data/transactions.csv")),
        "transaction_count": len(transactions),
        "product_count": len(set().union(*transactions)),
        "minimum_support": min_support,
        "minimum_support_count": threshold_count,
        "minimum_confidence": min_confidence,
        "effective_support": threshold_count / len(transactions),
        "itemsets": itemsets,
        "rules": serialized_rules,
        "itemset_count": len(itemsets),
        "rule_count": len(serialized_rules),
        "best_rule": serialized_rules[0] if serialized_rules else None,
    }
