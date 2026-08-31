from pathlib import Path
import re


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_app_selectors_exist_in_dashboard_markup():
    app_source = (PROJECT_DIR / "app.js").read_text()
    page_source = (PROJECT_DIR / "index.html").read_text()

    selectors = set(re.findall(r'\$\("#([^"]+)"\)', app_source))
    page_ids = set(re.findall(r'\bid="([^"]+)"', page_source))

    assert selectors <= page_ids
