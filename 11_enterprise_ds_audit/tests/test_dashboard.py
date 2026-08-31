import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DashboardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text()
        cls.app = (ROOT / "app.js").read_text()

    def test_finding_surface_has_all_filters_and_accessible_detail_target(self):
        for control in ('id="status-filter"', 'id="severity-filter"', 'id="category-filter"', 'id="finding-search"'):
            self.assertIn(control, self.html)
        self.assertIn('id="finding-drawer"', self.html)
        self.assertIn('role="dialog"', self.html)
        self.assertIn('data-open-check', self.app)
        self.assertIn('type="button"', self.app)

    def test_dashboard_uses_structured_evidence_and_decision_collections(self):
        self.assertIn("renderStructuredEvidence", self.app)
        self.assertIn("blocking_findings", self.app)
        self.assertIn("advisory_findings", self.app)
        self.assertIn("event.key === \"Escape\"", self.app)

    def test_stale_privacy_label_and_unused_report_fetch_are_removed(self):
        self.assertNotIn("Leakage &amp; privacy flags", self.html)
        self.assertNotIn('fetch("reports/audit_report.md"', self.app)


if __name__ == "__main__":
    unittest.main()
