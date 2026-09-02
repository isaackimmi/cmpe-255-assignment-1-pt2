"""Read-only access to the canonical checked-in transaction fixture."""
from __future__ import annotations

from analysis import load_transaction_rows, load_transactions


def transaction_sets() -> list[frozenset[str]]:
    return load_transactions()


def transaction_payload() -> list[dict]:
    return [
        {"transaction_id": row["transaction_id"], "items": sorted(row["items"])}
        for row in load_transaction_rows()
    ]
