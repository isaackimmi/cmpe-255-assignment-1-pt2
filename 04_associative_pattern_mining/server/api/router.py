"""Thin HTTP routes for the market-basket service."""
from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..schemas import ContextResponse, HealthResponse, ItemsetsResponse, RulesResponse, TransactionsResponse
from ..services.mining_service import InvalidMiningRequest, UnknownItem, item_context, mine, transactions

router = APIRouter()


def _mine_or_422(min_support: float, min_confidence: float, min_count: int) -> dict:
    try:
        return mine(min_support, min_confidence, min_count)
    except InvalidMiningRequest as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "basket-signals", "data_source": settings.data_source}


@router.get("/summary")
def summary(
    min_support: float = Query(0.25, gt=0.0, le=1.0),
    min_confidence: float = Query(0.60, gt=0.0, le=1.0),
    min_count: int = Query(1, ge=1),
):
    result = _mine_or_422(min_support, min_confidence, min_count)
    return {
        **{key: value for key, value in result.items() if key not in {"itemsets", "rules"}},
        "transactions": result["transaction_count"],
        "items": result["product_count"],
        "frequent_itemsets": result["itemset_count"],
        "rules": result["rule_count"],
        "effective_support_count": result["minimum_support_count"],
    }


@router.get("/transactions", response_model=TransactionsResponse)
def transaction_rows():
    return {"rows": transactions()}


@router.get("/itemsets", response_model=ItemsetsResponse)
def itemsets(
    min_support: float = Query(0.25, gt=0.0, le=1.0),
    min_count: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1),
):
    result = _mine_or_422(min_support, 0.0000001, min_count)
    rows = result["itemsets"]
    if size is not None:
        rows = [row for row in rows if row["size"] == size]
    return {"rows": rows, "transaction_count": result["transaction_count"], "effective_count": result["minimum_support_count"]}


@router.get("/rules", response_model=RulesResponse)
def rules(
    min_support: float = Query(0.25, gt=0.0, le=1.0),
    min_confidence: float = Query(0.60, gt=0.0, le=1.0),
    min_count: int = Query(1, ge=1),
    sort: str = Query("lift", pattern="^(lift|confidence|support)$"),
):
    result = _mine_or_422(min_support, min_confidence, min_count)
    rows = sorted(result["rules"], key=lambda row: (-row[sort], -row["confidence"], -row["support"], row["label"]))
    return {"rows": rows, "transaction_count": result["transaction_count"]}


@router.get("/context", response_model=ContextResponse)
def context(item: str = Query(..., min_length=1)):
    try:
        return item_context(item)
    except UnknownItem as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
