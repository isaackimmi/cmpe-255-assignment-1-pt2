from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_e2e_layers_exist_and_are_vite_fastapi_compatible():
    assert (ROOT / "client" / "package.json").exists()
    assert (ROOT / "client" / "vite.config.js").exists()
    assert (ROOT / "client" / "src" / "main.jsx").exists()
    assert (ROOT / "client" / "src" / "App.jsx").exists()
    assert len(list((ROOT / "client" / "src" / "components").rglob("*.jsx"))) >= 10
    assert (ROOT / "client" / "src" / "hooks" / "useBasketSignals.js").exists()
    assert (ROOT / "client" / "src" / "services" / "api.js").exists()
    assert (ROOT / "server" / "main.py").exists()
    assert (ROOT / "server" / "api" / "router.py").exists()
    assert (ROOT / "server" / "services" / "mining_service.py").exists()
    assert (ROOT / "server" / "requirements.txt").exists()
    assert (ROOT / "ml" / "pipeline.py").exists()
    assert (ROOT / "ml" / "mining.py").exists()
    assert (ROOT / "ml" / "serialization.py").exists()


def test_server_exposes_model_facing_endpoints():
    source = (ROOT / "server" / "api" / "router.py").read_text(encoding="utf-8")
    for endpoint in ("/api/health", "/api/summary", "/api/transactions", "/api/itemsets", "/api/rules", "/api/context"):
        assert endpoint.replace("/api", "") in source
    service = (ROOT / "server" / "services" / "mining_service.py").read_text(encoding="utf-8")
    assert "run_mining" in service
    assert "transaction_payload" in service
    assert "context_for_item" in service


def test_client_is_api_backed_and_surfaces_metric_denominators():
    api_source = (ROOT / "client" / "src" / "services" / "api.js").read_text(encoding="utf-8")
    hook_source = (ROOT / "client" / "src" / "hooks" / "useBasketSignals.js").read_text(encoding="utf-8")
    component_source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "client" / "src" / "components").rglob("*.jsx"))
    assert "fetch(`${API_BASE}/" in api_source
    assert "AbortController" in hook_source
    source = api_source + component_source
    assert "min_support" in source
    assert "min_confidence" in source
    assert "support_count" in source
    assert "conditional_probability" in source


def test_client_uses_react_and_radix_component_library():
    package = (ROOT / "client" / "package.json").read_text(encoding="utf-8")
    assert '"react"' in package
    assert '"@radix-ui/react-select"' in package
    assert '"@radix-ui/react-slider"' in package
