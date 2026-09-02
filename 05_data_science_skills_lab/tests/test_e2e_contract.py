from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_react_vite_client_has_composable_entrypoints():
    package = (ROOT / "client" / "package.json").read_text()
    html = (ROOT / "client" / "index.html").read_text()
    app = (ROOT / "client" / "src" / "App.jsx").read_text()
    api = (ROOT / "client" / "src" / "api" / "labApi.js").read_text()
    assert '"dev": "vite' in package
    assert '"react"' in package and '"@mui/material"' in package
    assert 'src="/src/main.jsx"' in html
    for component in ["AppShell", "MetricGrid", "ExplorerFilters", "EvidencePanels"]:
        assert component in app
    assert "VITE_API_URL" in api
    assert "/api/summary" in api and "/api/rows?" in api
    for route in ["/api/cleaning", "/api/classification", "/api/regression", "/api/clustering"]:
        assert route in (ROOT / "client" / "src" / "constants" / "modules.js").read_text()


def test_component_tree_has_reusable_boundaries():
    expected = [
        "components/layout/AppShell.jsx",
        "components/navigation/ModuleNav.jsx",
        "components/common/MetricCard.jsx",
        "components/metrics/MetricGrid.jsx",
        "components/filters/ExplorerFilters.jsx",
        "components/evidence/EvidencePanels.jsx",
        "components/modules/ModulePanel.jsx",
    ]
    assert all((ROOT / "client" / "src" / path).exists() for path in expected)


def test_fastapi_routes_services_and_schemas_are_modular():
    main = (ROOT / "server" / "main.py").read_text()
    routes = (ROOT / "server" / "routers" / "evidence.py").read_text()
    schemas = (ROOT / "server" / "schemas.py").read_text()
    service = (ROOT / "server" / "services" / "evidence.py").read_text()
    health = (ROOT / "server" / "routers" / "health.py").read_text()
    for route in ["/summary", "/cleaning", "/classification", "/regression", "/clustering", "/rows"]:
        assert route in routes
    assert "/health" in health and "include_router" in main and "CORSMiddleware" in main
    assert "plan must be one of" in schemas and "filtered_rows" in service


def test_ml_adapter_is_artifact_backed_and_not_browser_fitting():
    facade = (ROOT / "ml" / "pipeline.py").read_text()
    artifacts = (ROOT / "ml" / "artifacts.py").read_text()
    service = (ROOT / "ml" / "service.py").read_text()
    assert "load_artifacts" in facade and "load_clean" in service
    assert "does not silently retrain" in facade
    assert "REQUIRED_METRIC_SECTIONS" in artifacts


def test_artifact_adapter_has_schema_errors_and_one_authoritative_stylesheet():
    source = (ROOT / "ml" / "artifacts.py").read_text()
    assert "ArtifactContractError" in source and "missing required sections" in source
    assert (ROOT / "client" / "src" / "style.css").exists()
    assert not (ROOT / "client" / "src" / "styles.css").exists()
