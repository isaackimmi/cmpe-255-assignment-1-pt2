import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_health_and_transactions_routes():
    assert client.get("/api/health").json()["status"] == "ok"
    payload = client.get("/api/transactions").json()
    assert len(payload["rows"]) == 24
    assert payload["rows"][0] == {"transaction_id": "T001", "items": ["bread", "eggs", "milk"]}


def test_summary_itemsets_and_rules_match_canonical_shapes():
    summary = client.get("/api/summary", params={"min_support": 0.25, "min_confidence": 0.60, "min_count": 6})
    assert summary.status_code == 200
    assert summary.json()["minimum_support_count"] == 6
    assert summary.json()["transactions"] == summary.json()["transaction_count"] == 24
    assert summary.json()["frequent_itemsets"] == summary.json()["itemset_count"] == 18
    itemsets = client.get("/api/itemsets", params={"min_support": 0.25, "min_count": 6}).json()
    rules = client.get("/api/rules", params={"min_support": 0.25, "min_confidence": 0.60, "min_count": 6}).json()
    assert len(itemsets["rows"]) == 18
    assert len(rules["rows"]) == 15
    assert rules["rows"][0]["support_count"] == 6
    assert rules["rows"][0]["antecedent_count"] > 0
    assert rules["rows"][0]["consequent_count"] > 0


def test_routes_reject_impossible_count_and_unknown_context_item():
    assert client.get("/api/summary", params={"min_count": 25}).status_code == 422
    assert client.get("/api/itemsets", params={"min_count": 25}).status_code == 422
    assert client.get("/api/rules", params={"min_count": 25}).status_code == 422
    assert client.get("/api/context", params={"item": "unicorn"}).status_code == 404


def test_context_route_discloses_conditional_view():
    response = client.get("/api/context", params={"item": "bread"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["basket_count"] == 19
    assert "not an association rule" in payload["interpretation"]
