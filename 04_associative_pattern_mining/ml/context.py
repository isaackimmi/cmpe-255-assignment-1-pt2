"""Conditional co-occurrence context for the basket explorer."""
from __future__ import annotations

from .repository import transaction_payload


def context_for_item(item: str) -> dict:
    rows = transaction_payload()
    matching = [row for row in rows if item in row["items"]]
    if not matching:
        raise ValueError(f"No baskets contain {item!r}")
    candidates = sorted({value for row in matching for value in row["items"]} - {item})
    counts = {candidate: sum(candidate in row["items"] for row in matching) for candidate in candidates}
    return {
        "item": item,
        "basket_count": len(matching),
        "candidates": [
            {"item": candidate, "count": count, "conditional_probability": count / len(matching)}
            for candidate, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
        ],
        "interpretation": "P(candidate | selected item); this context view is not an association rule.",
    }
