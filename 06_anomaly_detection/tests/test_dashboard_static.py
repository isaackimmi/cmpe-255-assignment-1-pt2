from pathlib import Path
import re


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_app_selectors_exist_in_dashboard_markup():
    app_source = (PROJECT_DIR / "app.js").read_text()
    page_source = (PROJECT_DIR / "index.html").read_text()

    selectors = set(re.findall(r'\$\("#([^"]+)"\)', app_source))
    page_ids = set(re.findall(r'\bid="([^"]+)"', page_source))

    assert selectors <= page_ids


def test_dashboard_exposes_leakage_safe_disclosures_and_score_explorer():
    page_source = (PROJECT_DIR / "index.html").read_text()
    app_source = (PROJECT_DIR / "app.js").read_text()

    assert "oracle benchmark" in page_source
    assert "must not be used to select a production threshold" in page_source
    assert "observations.json" in page_source
    assert "score-plot" in page_source
    assert "currentFlaggedRows" in app_source
    assert "renderCategoryBars" in app_source
    assert 'id="methodology"' in page_source
    assert '<div class="stamp-ring">42</div>' not in page_source
