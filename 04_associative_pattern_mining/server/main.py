"""Transport layer for the reproducible Project 04 mining service."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.pipeline import context_for_item, run_mining, transaction_payload  # noqa: E402

app = FastAPI(title="Basket Signals API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET"], allow_headers=["*"])


def _run(min_support: float, min_confidence: float, min_count: int) -> dict:
    try:
        return run_mining(min_support=min_support, min_confidence=min_confidence, min_count=min_count)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "basket-signals", "data_source": "data/transactions.csv"}


@app.get("/api/summary")
def summary(min_support: float = Query(0.25, gt=0.0, le=1.0), min_confidence: float = Query(0.60, gt=0.0, le=1.0), min_count: int = Query(1, ge=1)):
    result = _run(min_support, min_confidence, min_count)
    return {
        **{key: value for key, value in result.items() if key not in {"itemsets", "rules"}},
        # These aliases are the intentionally small transport contract consumed by the client.
        "transactions": result["transaction_count"],
        "items": result["product_count"],
        "frequent_itemsets": result["itemset_count"],
        "rules": result["rule_count"],
        "effective_support_count": result["minimum_support_count"],
    }


@app.get("/api/transactions")
def transactions():
    return {"rows": transaction_payload()}


@app.get("/api/itemsets")
def itemsets(min_support: float = Query(0.25, gt=0.0, le=1.0), min_count: int = Query(1, ge=1), size: int | None = Query(None, ge=1)):
    result = _run(min_support, 0.0000001, min_count)
    rows = result["itemsets"]
    if size is not None:
        rows = [row for row in rows if row["size"] == size]
    return {"rows": rows, "transaction_count": result["transaction_count"], "effective_count": result["minimum_support_count"]}


@app.get("/api/rules")
def rules(min_support: float = Query(0.25, gt=0.0, le=1.0), min_confidence: float = Query(0.60, gt=0.0, le=1.0), min_count: int = Query(1, ge=1), sort: str = Query("lift", pattern="^(lift|confidence|support)$")):
    result = _run(min_support, min_confidence, min_count)
    rows = sorted(result["rules"], key=lambda row: (-row[sort], -row["confidence"], -row["support"], row["label"]))
    return {"rows": rows, "transaction_count": result["transaction_count"]}


@app.get("/api/context")
def context(item: str = Query(..., min_length=1)):
    try:
        return context_for_item(item.strip())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
