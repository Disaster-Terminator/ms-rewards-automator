"""Failure screenshot and diagnostic capture utilities."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Page


def _get_run_dir() -> Path:
    """Get or create the current run directory."""
    base_dir = Path("logs/e2e")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing latest symlink or create new run dir
    latest_link = base_dir / "latest"
    if latest_link.is_symlink():
        run_dir = Path(os.readlink(latest_link))
        if run_dir.exists():
            return run_dir

    # Create new run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{timestamp}"
    run_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (run_dir / "screenshots").mkdir(exist_ok=True)
    (run_dir / "dom_snapshots").mkdir(exist_ok=True)
    (run_dir / "console_logs").mkdir(exist_ok=True)

    # Update latest symlink
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(run_dir.name)

    return run_dir


def _sanitize_node_id(node_id: str) -> str:
    """Sanitize pytest node ID for use in filename."""
    # Replace :: and / with underscores, remove special chars
    sanitized = re.sub(r"[^\w\-_.]", "_", node_id.replace("::", "__").replace("/", "_"))
    return sanitized[:100]  # Truncate to reasonable length


async def capture_failure_screenshot(
    page: Page,
    test_name: str,
    request: Any,
) -> dict[str, str]:
    """
    Capture failure diagnostic data: screenshot, DOM snapshot, console logs.

    Args:
        page: Playwright page object
        test_name: Human-readable test name
        request: pytest request object for node ID

    Returns:
        Dict with paths to captured artifacts
    """
    run_dir = _get_run_dir()
    node_id = _sanitize_node_id(request.node.nodeid)

    artifacts = {}

    # Capture full page screenshot
    screenshot_path = run_dir / "screenshots" / f"{node_id}.png"
    await page.screenshot(path=str(screenshot_path), full_page=True)
    artifacts["screenshot"] = str(screenshot_path)

    # Capture DOM snapshot
    dom_path = run_dir / "dom_snapshots" / f"{node_id}.html"
    content = await page.content()
    dom_path.write_text(content, encoding="utf-8")
    artifacts["dom_snapshot"] = str(dom_path)

    # Capture console logs (optional)
    console_logs = getattr(page, "_e2e_console_logs", [])
    if console_logs:
        console_path = run_dir / "console_logs" / f"{node_id}.json"
        console_path.write_text(json.dumps(console_logs, indent=2), encoding="utf-8")
        artifacts["console_logs"] = str(console_path)

    return artifacts
