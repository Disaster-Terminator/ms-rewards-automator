"""
E2E test configuration for RewardsCore.

Provides:
- Playwright browser fixtures (session-scoped browser, function-scoped contexts)
- Test configuration via E2E_* environment variables
- Automatic cleanup and failure screenshot capture
"""

from typing import Any, Generator

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from tests.e2e.helpers.environment import get_environment_type, is_ci_environment

# E2E-specific default configuration overrides
# Uses E2E_* namespace to avoid conflicts with MS_REWARDS_*
E2E_DEFAULT_CONFIG = {
    "search": {
        "desktop_count": 2,  # E2E_SEARCH_COUNT default
    },
    "browser": {
        "headless": False,  # E2E_HEADLESS default (false for local, true for CI)
    },
    "task_system": {
        "enabled": False,
    },
    "scheduler": {
        "enabled": False,
    },
    "notification": {
        "enabled": False,
    },
    "diagnosis": {
        "enabled": True,
    },
}


@pytest.fixture(scope="session")
def e2e_config() -> dict[str, Any]:
    """
    Provide E2E test configuration.

    Configuration priority:
    1. E2E_* environment variables
    2. E2E_DEFAULT_CONFIG values
    """
    import os

    config = E2E_DEFAULT_CONFIG.copy()

    # Override from environment variables
    if os.environ.get("E2E_SEARCH_COUNT"):
        config["search"]["desktop_count"] = int(os.environ["E2E_SEARCH_COUNT"])

    # Headless mode: default to True in CI, False locally
    if os.environ.get("E2E_HEADLESS"):
        config["browser"]["headless"] = os.environ["E2E_HEADLESS"].lower() == "true"
    else:
        config["browser"]["headless"] = is_ci_environment()

    return config


@pytest.fixture(scope="session")
async def browser(e2e_config: dict[str, Any]) -> Generator[Browser, None, None]:
    """
    Provide a session-scoped Playwright browser instance.

    Uses Chromium only, consistent with main app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=e2e_config["browser"]["headless"],
        )
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """
    Provide a fresh browser context for each test.

    Ensures 100% isolation between tests.
    """
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture(scope="function")
async def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Provide a fresh page for each test with automatic cleanup.

    Ensures page is closed after test.
    """
    page = await context.new_page()

    # Set up console log collection
    console_logs: list[dict[str, Any]] = []
    page._e2e_console_logs = console_logs  # type: ignore[attr-defined]

    def on_console(msg):
        console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', '')}",
        })

    page.on("console", on_console)

    yield page

    # Cleanup: ensure page is closed
    if not page.is_closed():
        await page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture failure screenshots and diagnostics.

    Uses in-test capture approach.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Store failure info for potential cleanup
        item._e2e_failed = True
        item._e2e_failure_repr = report.longreprtext


@pytest.fixture(autouse=True)
async def _capture_failure_on_error(request: Any, page: Page):
    """
    Automatically capture failure artifacts when test fails.

    Uses try/except in-test capture.
    """
    yield

    # Check if test failed
    if hasattr(request.node, "_e2e_failed") and request.node._e2e_failed:
        from tests.e2e.helpers.screenshot import capture_failure_screenshot

        artifacts = await capture_failure_screenshot(
            page,
            test_name=request.node.name,
            request=request,
        )
        # Log artifacts location
        import logging
        logging.error(f"Test failed. Artifacts saved: {artifacts}")
