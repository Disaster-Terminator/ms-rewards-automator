#!/usr/bin/env python
"""
Send test result notifications to Slack via webhook.
Usage:
    python tests/e2e/notifications/slack_notifier.py reports/summary.json
"""
import json
import sys
import httpx
from datetime import datetime, timezone
from typing import Dict

def send_slack_notification(webhook_url: str, report: Dict):
    """Post formatted message to Slack channel."""
    pass_rate = report.get("pass_rate", 0)
    status = "✅ PASS" if pass_rate >= 90 else "⚠️ WARNING" if pass_rate >= 70 else "❌ FAIL"

    color = "good" if pass_rate >= 90 else "warning" if pass_rate >= 70 else "danger"

    payload = {
        "attachments": [{
            "color": color,
            "title": f"E2E Test Run - {status}",
            "fields": [
                {"title": "Total", "value": str(report["total"]), "short": True},
                {"title": "Passed", "value": str(report["passed"]), "short": True},
                {"title": "Failed", "value": str(report["failed"]), "short": True},
                {"title": "Skipped", "value": str(report["skipped"]), "short": True},
                {"title": "Pass Rate", "value": f"{pass_rate:.1f}%", "short": True}
            ],
            "footer": "RewardsCore CI",
            "ts": int(datetime.now(timezone.utc).timestamp())
        }]
    }

    with httpx.Client() as client:
        response = client.post(webhook_url, json=payload)
        response.raise_for_status()

def main():
    if len(sys.argv) < 3:
        print("Usage: slack_notifier.py <summary_json> <slack_webhook_url>")
        return 1

    summary_path = sys.argv[1]
    webhook_url = sys.argv[2]

    try:
        with open(summary_path) as f:
            report = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load summary JSON: {e}")
        return 1

    try:
        send_slack_notification(webhook_url, report)
        print("✓ Slack notification sent")
        return 0
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
