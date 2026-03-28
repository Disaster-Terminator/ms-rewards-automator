#!/usr/bin/env python
"""
Generate comprehensive E2E test reports in JSON and HTML formats.
Usage:
    pytest tests/e2e/ --junitxml=pytest.xml --json-report --report-dir=reports/
    python tests/e2e/reporting/generate_report.py reports/
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

def load_junit_xml(paths: List[str]) -> Dict:
    """Parse one or more pytest JUnit XML files into a single structured report."""
    import xml.etree.ElementTree as ET

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "tests": []
    }

    for path in paths:
        if not os.path.exists(path):
            print(f"WARNING: JUnit XML not found at {path}, skipping...")
            continue
            
        tree = ET.parse(path)
        root = tree.getroot()

        for testcase in root.iter("testcase"):
            report["total_tests"] += 1
            classname = testcase.get("classname", "")
            name = testcase.get("name", "")
            time = float(testcase.get("time", 0))

            status = "passed"
            failure_msg = None
            error_msg = None

            # Check for failures
            failure = testcase.find("failure")
            if failure is not None:
                status = "failed"
                failure_msg = failure.get("message", "")
                error_msg = failure.text

            # Check for errors (different from failure in pytest)
            error = testcase.find("error")
            if error is not None:
                status = "error"
                error_msg = error.get("message", "")

            # Check for skips
            skipped = testcase.find("skipped")
            if skipped is not None:
                status = "skipped"
                error_msg = skipped.get("message", "")

            test_result = {
                "classname": classname,
                "name": name,
                "status": status,
                "time": time,
                "failure": failure_msg,
                "error": error_msg
            }
            report["tests"].append(test_result)

            # Count statuses
            if status == "passed":
                report["passed"] += 1
            elif status in ["failed", "error"]:
                report["failed"] += 1
            elif status == "skipped":
                report["skipped"] += 1

    return report

def generate_html_report(report: Dict, output_path: str):
    """Generate human-readable HTML report."""
    pass_rate = (report["passed"] / report["total_tests"] * 100) if report["total_tests"] > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>E2E Test Report</title>
    <style>
        body {{ font-family: sans-serif; margin: 2rem; }}
        .summary {{ display: flex; gap: 2rem; margin-bottom: 2rem; }}
        .stat {{ padding: 1rem 2rem; border-radius: 8px; color: white; font-weight: bold; }}
        .passed {{ background: #28a745; }}
        .failed {{ background: #dc3545; }}
        .skipped {{ background: #ffc107; }}
        .total {{ background: #17a2b8; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 2rem; }}
        th, td {{ padding: 0.75rem; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f4f4f4; }}
        .status-PASSED {{ color: #28a745; font-weight: bold; }}
        .status-FAILED {{ color: #dc3545; font-weight: bold; }}
        .status-ERROR {{ color: #dc3545; font-weight: bold; }}
        .status-SKIPPED {{ color: #ffc107; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>E2E Test Report</h1>
    <p><strong>Generated:</strong> {report["generated_at"]}</p>

    <div class="summary">
        <div class="stat total">Total: {report["total_tests"]}</div>
        <div class="stat passed">Passed: {report["passed"]}</div>
        <div class="stat failed">Failed: {report["failed"]}</div>
        <div class="stat skipped">Skipped: {report["skipped"]}</div>
    </div>

    <h2>Pass Rate: {pass_rate:.1f}%</h2>

    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test</th>
                <th>Status</th>
                <th>Time (s)</th>
                <th>Failure/Error</th>
            </tr>
        </thead>
        <tbody>
"""

    for test in report["tests"]:
        status_class = f"status-{test['status'].upper()}"
        failure_display = test.get("failure") or test.get("error") or ""
        html += f"""            <tr>
                <td>{test["classname"]}.{test["name"]}</td>
                <td class="{status_class}">{test["status"].upper()}</td>
                <td>{test["time"]:.2f}</td>
                <td>{failure_display}</td>
            </tr>
"""

    html += """        </tbody>
    </table>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    if len(sys.argv) < 2:
        print("Usage: generate_report.py <report_dir> [junit_xml_path1] [junit_xml_path2] ...")
        return 1

    report_dir = Path(sys.argv[1])
    report_dir.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 2:
        junit_paths = sys.argv[2:]
    else:
        junit_paths = [str(report_dir / "pytest.xml")]
    
    # Filter only existing paths
    existing_junit_paths = [p for p in junit_paths if os.path.exists(p)]
    if not existing_junit_paths:
        print(f"ERROR: No JUnit XML files found at {junit_paths}")
        return 1

    print(f"Loading JUnit XML files: {existing_junit_paths}...")
    report = load_junit_xml(existing_junit_paths)

    # Save JSON
    json_path = report_dir / "report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"✓ JSON report: {json_path}")

    # Save HTML
    html_path = report_dir / "report.html"
    generate_html_report(report, str(html_path))
    print(f"✓ HTML report: {html_path}")

    # Summary
    pass_rate = (report["passed"] / report["total_tests"] * 100) if report["total_tests"] > 0 else 0
    print(f"\n📊 Summary: {report['passed']}/{report['total_tests']} passed ({pass_rate:.1f}%)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
