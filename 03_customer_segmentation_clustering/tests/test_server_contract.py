import json
from pathlib import Path
import shutil
import pytest

ROOT = Path(__file__).parents[1]

def test_e2e_directories_and_client_contract_exist():
    assert (ROOT / "client/package.json").exists()
    package = json.loads((ROOT / "client/package.json").read_text())
    assert {"react", "react-dom", "@mui/material"}.issubset(package["dependencies"])
    assert (ROOT / "client/src/main.jsx").exists()
    assert len(list((ROOT / "client/src/components").rglob("*.jsx"))) >= 10
    assert (ROOT / "client/src/hooks/useSegmentationData.js").exists()
    assert (ROOT / "server/routers/evidence.py").read_text().count('@router.get') >= 5
    assert (ROOT / "server/routers/segmentation.py").read_text().count('@router.') >= 3
    assert (ROOT / "server/services/artifacts.py").exists()
    assert (ROOT / "ml/pipeline.py").exists()
    assert (ROOT / "ml/scoring.py").exists()

def test_api_artifacts_have_required_contract():
    summary = json.loads((ROOT / "artifacts/summary.json").read_text())
    manifest = json.loads((ROOT / "artifacts/manifest.json").read_text())
    assert summary["selected_k"] == manifest["selected_k"]
    assert summary["features"] == manifest["features"]
    assert set(["summary.json", "explorer_points.csv", "customer_segments.csv"]).issubset(manifest["hashes"])

def test_scoring_adapter_uses_domain_validated_feature_contract():
    from ml.pipeline import score_observation
    result = score_observation({"annual_income_k": 72, "spend_score": 78, "purchase_frequency": 7, "avg_order_value": 68})
    assert result["cluster"] in {0, 1, 2}
    assert len(result["distances"]) == 3
    assert result["assignment_margin"] >= 0

def test_ml_adapter_matches_canonical_path_for_both_preprocessing_variants():
    import pandas as pd
    from ml.pipeline import score_observation
    from src.experiment import FEATURES, fit_segmenter, make_dataset, score_customers
    values = {"annual_income_k": 72, "spend_score": 78, "purchase_frequency": 7, "avg_order_value": 68}
    incoming = pd.DataFrame([values], columns=FEATURES)
    for preprocessing in ("standard", "log1p"):
        fitted = fit_segmenter(make_dataset(), preprocessing, 3)
        expected = int(score_customers(incoming, fitted).iloc[0])
        assert score_observation(values, preprocessing=preprocessing, k=3)["cluster"] == expected

def test_api_routes_validate_evidence_and_support_filters():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from server.app import app
    client = TestClient(app)
    status = client.get("/api/evidence-status")
    assert status.status_code == 200
    assert status.json()["valid"] is True
    assert client.get("/api/points?cluster=0").status_code == 200
    assert all(row["cluster"] == 0 for row in client.get("/api/points?cluster=0").json())
    profiles = client.get("/api/profiles").json()
    assert profiles and all(profile["name_basis"]["rank"] for profile in profiles)

def test_api_reports_corrupt_artifacts_without_green_status(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import server.app as api
    from server.services.artifacts import repository
    shutil.copytree(ROOT / "artifacts", tmp_path / "artifacts")
    (tmp_path / "artifacts" / "manifest.json").write_text("not json")
    monkeypatch.setattr(repository, "root", tmp_path / "artifacts")
    response = TestClient(api.app).get("/api/evidence-status")
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert TestClient(api.app).get("/api/summary").status_code == 503

def test_api_rejects_out_of_domain_observation():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from server.app import app
    response = TestClient(app).post("/api/score", json={"annual_income_k": 1, "spend_score": 50, "purchase_frequency": 3, "avg_order_value": 50})
    assert response.status_code == 422
