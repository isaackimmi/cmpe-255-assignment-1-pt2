import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_e2e_directories_and_client_contract_exist():
    assert (ROOT / "client/package.json").exists()
    assert (ROOT / "client/src/main.js").read_text().startswith("import './styles.css';")
    assert (ROOT / "server/app.py").read_text().count('@app.get') >= 5
    assert (ROOT / "server/app.py").read_text().count('@app.') >= 7
    assert (ROOT / "ml/pipeline.py").exists()

def test_api_artifacts_have_required_contract():
    summary = json.loads((ROOT / "artifacts/summary.json").read_text())
    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    assert summary["selected_k"] == manifest["selected_k"]
    assert summary["features"] == manifest["features"]
    assert set(["summary.json", "explorer_points.csv", "customer_segments.csv"]).issubset(manifest["hashes"])
