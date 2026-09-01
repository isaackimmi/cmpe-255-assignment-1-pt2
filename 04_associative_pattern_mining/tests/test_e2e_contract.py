from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_e2e_layers_exist_and_are_vite_fastapi_compatible():
    assert (ROOT / "client" / "package.json").exists()
    assert (ROOT / "client" / "vite.config.js").exists()
    assert (ROOT / "client" / "src" / "main.js").exists()
    assert (ROOT / "server" / "main.py").exists()
    assert (ROOT / "server" / "requirements.txt").exists()
    assert (ROOT / "ml" / "pipeline.py").exists()


def test_server_exposes_model_facing_endpoints():
    source = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
    for endpoint in ("/api/health", "/api/summary", "/api/transactions", "/api/itemsets", "/api/rules", "/api/context"):
        assert endpoint in source
    assert "run_mining" in source
    assert "transaction_payload" in source
    assert "context_for_item" in source


def test_client_is_api_backed_and_surfaces_metric_denominators():
    source = (ROOT / "client" / "src" / "main.js").read_text(encoding="utf-8")
    assert "fetch(`/api/" in source
    assert "min_support" in source
    assert "min_confidence" in source
    assert "support_count" in source
    assert "conditional_probability" in source
