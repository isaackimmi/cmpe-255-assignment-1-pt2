import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vite_client_has_expected_entrypoints():
    package = (ROOT / "client" / "package.json").read_text()
    html = (ROOT / "client" / "index.html").read_text()
    js = (ROOT / "client" / "src" / "main.js").read_text()
    assert '"dev": "vite' in package
    assert 'src="/src/main.js"' in html
    assert "/api/summary" in js
    assert "data-module" in js
    assert "VITE_API_URL" in js
    assert "/api/rows?" in js
    for route in ["/api/cleaning", "/api/classification", "/api/regression", "/api/clustering"]:
        assert route in js


def test_fastapi_routes_and_cors_are_declared():
    source = (ROOT / "server" / "main.py").read_text()
    tree = ast.parse(source)
    routes = {node.decorator_list[0].args[0].value for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.decorator_list and isinstance(node.decorator_list[0], ast.Call) and node.decorator_list[0].args}
    assert {"/api/health", "/api/summary", "/api/cleaning", "/api/classification", "/api/regression", "/api/clustering", "/api/rows"}.issubset(routes)
    assert "CORSMiddleware" in source
    assert "plan must be one of" in source
    assert "renewal must be one of" in source
    assert "cluster must be all or" in source


def test_ml_adapter_is_artifact_backed_and_not_browser_fitting():
    source = (ROOT / "ml" / "pipeline.py").read_text()
    assert "load_artifacts" in source
    assert "load_clean" in source
    assert "does not silently retrain" in source


def test_artifact_adapter_has_schema_errors_and_one_authoritative_stylesheet():
    source = (ROOT / "ml" / "pipeline.py").read_text()
    assert "ArtifactContractError" in source
    assert "missing required sections" in source
    assert (ROOT / "client" / "src" / "style.css").exists()
    assert not (ROOT / "client" / "src" / "styles.css").exists()
