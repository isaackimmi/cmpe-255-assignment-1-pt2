"""Translate model-layer exceptions into transport-neutral service errors."""
from ml.pipeline import context_for_item, run_mining, transaction_payload


class InvalidMiningRequest(ValueError):
    pass


class UnknownItem(ValueError):
    pass


def mine(min_support: float, min_confidence: float, min_count: int) -> dict:
    try:
        return run_mining(min_support=min_support, min_confidence=min_confidence, min_count=min_count)
    except ValueError as exc:
        raise InvalidMiningRequest(str(exc)) from exc


def transactions() -> list[dict]:
    return transaction_payload()


def item_context(item: str) -> dict:
    try:
        return context_for_item(item.strip())
    except ValueError as exc:
        raise UnknownItem(str(exc)) from exc
