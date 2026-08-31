#!/usr/bin/env python3
"""Generate a deterministic sample and run the Project 11 governance audit."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from enterprise_audit import generate_sample, audit_dataset, write_report  # noqa: E402


def main() -> int:
    data_dir = ROOT / "artifacts"
    report_dir = ROOT / "reports"
    data_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)
    csv_path = data_dir / "sample_customers.csv"
    generate_sample(csv_path, seed=255)
    result = audit_dataset(csv_path, seed=255)
    write_report(result, report_dir / "audit_report.md", report_dir / "audit_results.json")
    print(result["summary"])
    print(f"Report: {report_dir / 'audit_report.md'}")
    # Findings are data, not a process failure: the audit should be CI-friendly
    # while its report carries the release decision.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
