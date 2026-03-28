# E2E Test Reporting & Notifications

## Reports Generated

### Per-Run Files

Each E2E test run produces several report files for both machine processing and human review.

- **`reports/summary.json`**: A high-level JSON object containing pass/fail/skip counts and the overall pass rate. This is used by the Slack notifier and CI dashboard.
- **`reports/report.json`**: A detailed JSON report generated from pytest JUnit XML, including per-test status, execution time, and failure messages.
- **`reports/report.html`**: A human-readable HTML dashboard for reviewing the results of a specific run.

### Artifact Directory Structure

```
logs/e2e/
├── reports/
│   ├── summary.json          # Aggregated pass/fail/skip counts
│   ├── report.json           # Detailed test-by-test results
│   └── report.html           # Human-readable HTML report
├── screenshots/
│   └── {test_name}_{timestamp}.png  # Captured on failure
└── diagnosis/
    └── {timestamp}/
        ├── summary.json
        └── screenshots/
```

### CI Artifacts

The GitHub Actions workflows are configured to upload all reporting and diagnostic files as artifacts.

1.  **Test Results**: Exported as JUnit XML (`pytest-results.xml`).
2.  **Screenshots**: Uploaded as a separate artifact on failure for quick review.
3.  **Full Reports**: The entire `reports/` directory is bundled and uploaded.

To access these, go to the **Actions** tab in GitHub, select the specific run, and scroll down to the **Artifacts** section.

## Slack Notifications

### Setup

To enable Slack notifications, you must configure a Slack Incoming Webhook and add it to your repository secrets.

1.  **Create Slack Incoming Webhook**:
    - Go to your Slack App configuration page (https://api.slack.com/apps).
    - Enable **Incoming Webhooks**.
    - Click **Add New Webhook to Workspace** and select a channel.
    - Copy the generated Webhook URL.

2.  **Add Secret to GitHub**:
    - Navigate to your repository's **Settings** → **Secrets and variables** → **Actions**.
    - Create a **New repository secret**.
    - **Name**: `SLACK_WEBHOOK_URL`
    - **Secret**: (Paste the Webhook URL you copied).

### Notification Behavior

The Slack notifier is currently configured to send a color-coded message:
- 🟩 **Green**: Pass rate ≥ 90%
- 🟨 **Yellow**: Pass rate between 70% and 90%
- 🟥 **Red**: Pass rate < 70%

Notifications include a summary of the test counts and a link to the CI run.

## CI Dashboard

A static dashboard is available at `docs/ci-dashboard.html`. When GitHub Pages is enabled for the `docs/` directory, this dashboard can be accessed at:

`https://<your-username>.github.io/<repo-name>/ci-dashboard.html`

The dashboard automatically attempts to fetch `reports/summary.json` to display the latest run status and metrics. It refreshes every 5 minutes.

## Automated Cleanup

To prevent logs and screenshots from consuming excessive disk space, a cleanup script is provided.

### Manual Cleanup
```bash
python tools/cleanup_artifacts.py --days 30 logs/e2e/
```

### Scheduled Cleanup
For long-running local environments or servers, it is recommended to add a cron job:

```bash
# Example crontab entry for daily cleanup at 2:00 AM
0 2 * * * cd /path/to/repo && python tools/cleanup_artifacts.py --days 30 logs/e2e/
```

## Troubleshooting Reports

If reports are not generating as expected:
1.  **Check pytest options**: Ensure you are running pytest with `--junitxml=reports/pytest.xml` or that `E2E_REPORT_DIR` is set.
2.  **Directory Permissions**: Ensure the runner has write access to the `reports/` directory.
3.  **JSON Errors**: If `summary.json` is malformed, check the `pytest_terminal_summary` implementation in `tests/e2e/conftest.py`.

## Customization

You can customize the reporting behavior by editing:
- `tests/e2e/reporting/generate_report.py`: For changes to HTML/JSON structure.
- `tests/e2e/conftest.py`: For changes to how metrics are gathered at the end of a run.
- `tests/e2e/notifications/slack_notifier.py`: For changes to Slack message formatting.
