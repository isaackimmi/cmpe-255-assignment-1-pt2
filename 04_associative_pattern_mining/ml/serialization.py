"""JSON-safe serializers for Apriori itemsets and association rules."""
from __future__ import annotations

from analysis import support_count


def serialize_itemsets(frequent: dict, transactions: list[frozenset[str]]) -> list[dict]:
    rows = [
        {
            "items": sorted(items),
            "label": " + ".join(sorted(items)),
            "support": support,
            "count": support_count(items, transactions),
            "size": len(items),
        }
        for items, support in frequent.items()
    ]
    return sorted(rows, key=lambda row: (-row["support"], row["label"]))


def serialize_rules(rules: list[dict], transactions: list[frozenset[str]]) -> list[dict]:
    serialized = []
    for rule in rules:
        antecedent = rule["antecedent"]
        consequent = rule["consequent"]
        serialized.append({
            "antecedent": sorted(antecedent),
            "consequent": sorted(consequent),
            "label": f"{' + '.join(sorted(antecedent))} → {' + '.join(sorted(consequent))}",
            "support": rule["support"],
            "support_count": support_count(antecedent | consequent, transactions),
            "antecedent_count": support_count(antecedent, transactions),
            "consequent_count": support_count(consequent, transactions),
            "confidence": rule["confidence"],
            "lift": rule["lift"],
        })
    return serialized
