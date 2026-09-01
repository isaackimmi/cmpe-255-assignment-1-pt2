"""Serializable adapter around the audited Apriori implementation."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import association_rules, apriori, load_transaction_rows, load_transactions, minimum_support_count, support_count


def run_mining(min_support: float = 0.25, min_confidence: float = 0.60, min_count: int = 1) -> dict:
    """Run the reproducible model layer and return JSON-friendly records."""
    transactions = load_transactions()
    rows = load_transaction_rows()
    if not isinstance(min_count, int) or isinstance(min_count, bool) or min_count < 1:
        raise ValueError("min_count must be a positive integer")
    if min_count > len(transactions):
        raise ValueError(f"min_count cannot exceed transaction count ({len(transactions)})")
    frequent = apriori(transactions, min_support=min_support)
    threshold_count = max(minimum_support_count(min_support, len(transactions)), min_count)
    frequent = {items: value for items, value in frequent.items() if support_count(items, transactions) >= threshold_count}
    rules = association_rules(frequent, min_confidence=min_confidence)
    itemsets = [
        {"items": sorted(items), "label": " + ".join(sorted(items)), "support": value,
         "count": support_count(items, transactions), "size": len(items)}
        for items, value in frequent.items()
    ]
    itemsets.sort(key=lambda row: (-row["support"], row["label"]))
    serialized_rules = []
    for rule in rules:
        antecedent = rule["antecedent"]
        consequent = rule["consequent"]
        serialized_rules.append({
            "antecedent": sorted(antecedent), "consequent": sorted(consequent),
            "label": f"{' + '.join(sorted(antecedent))} → {' + '.join(sorted(consequent))}",
            "support": rule["support"],
            "support_count": support_count(antecedent | consequent, transactions),
            "antecedent_count": support_count(antecedent, transactions),
            "consequent_count": support_count(consequent, transactions),
            "confidence": rule["confidence"], "lift": rule["lift"],
        })
    return {
        "data_source": str(Path("data/transactions.csv")),
        "transaction_count": len(rows),
        "product_count": len(set().union(*transactions)),
        "minimum_support": min_support,
        "minimum_support_count": threshold_count,
        "minimum_confidence": min_confidence,
        "effective_support": threshold_count / len(transactions),
        "itemsets": itemsets, "rules": serialized_rules,
        "itemset_count": len(itemsets), "rule_count": len(serialized_rules),
        "best_rule": serialized_rules[0] if serialized_rules else None,
    }


def transaction_payload() -> list[dict]:
    return [{"transaction_id": row["transaction_id"], "items": sorted(row["items"])} for row in load_transaction_rows()]


def context_for_item(item: str) -> dict:
    rows = transaction_payload()
    matching = [row for row in rows if item in row["items"]]
    if not matching:
        raise ValueError(f"No baskets contain {item!r}")
    counts = {candidate: sum(candidate in row["items"] for row in matching)
              for candidate in sorted({value for row in matching for value in row["items"]} - {item})}
    return {
        "item": item, "basket_count": len(matching),
        "candidates": [{"item": candidate, "count": count, "conditional_probability": count / len(matching)}
                       for candidate, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))],
        "interpretation": "P(candidate | selected item); this context view is not an association rule.",
    }
