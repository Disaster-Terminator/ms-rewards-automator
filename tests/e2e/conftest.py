"""
E2E test configuration for RewardsCore.

Provides:
- Playwright browser fixtures (session-scoped browser, function-scoped contexts)
- Test configuration via E2E_* environment variables
- Automatic cleanup and failure screenshot capture
"""

import os
from typing import Any, Generator, Dict

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from tests.e2e.helpers.environment import get_environment_type, is_ci_environment

# Register pytest-asyncio plugin for pytest 9.x compatibility
pytest_plugins = ["pytest_asyncio"]

# E2E-specific default configuration overrides
# Uses E2E_* namespace to avoid conflicts with MS_REWARDS_*
E2E_DEFAULT_CONFIG = {
    "search": {
        "desktop_count": 2,  # E2E_SEARCH_COUNT default
    },
    "browser": {
        "headless": True,  # E2E_HEADLESS default (true for both local and CI)
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

    # Headless mode: default to True locally and in CI, unless E2E_HEADLESS=false
    if os.environ.get("E2E_HEADLESS"):
        config["browser"]["headless"] = os.environ["E2E_HEADLESS"].lower() == "true"
    else:
        config["browser"]["headless"] = True

    return config


@pytest.fixture(scope="function")
async def browser(e2e_config: dict[str, Any]) -> Generator[Browser, None, None]:
    """
    Provide a function-scoped Playwright browser instance.

    Changed from session to function scope to avoid asyncio deadlock in WSL
    with pytest-asyncio 1.3.0 + asyncio_default_fixture_loop_scope="session".
    Performance impact: browser launches once per test (acceptable for smoke tests).
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
        from tests.e2e.helpers.diagnostic_report import save_login_diagnostic

        # Save standard failure screenshot
        artifacts = await capture_failure_screenshot(
            page,
            test_name=request.node.name,
            request=request,
        )
        # Save specialized login diagnostic data for login tests
        if "login" in request.node.name.lower() or "login" in str(request.node.fspath).lower():
            diagnostic_info = await save_login_diagnostic(
                page,
                test_name=request.node.name,
                failure_repr=getattr(request.node, "_e2e_failure_repr", "No repr")
            )
            # Add to artifacts
            artifacts.update(diagnostic_info)

        # Log artifacts location
        import logging
        logging.error(f"Test failed. Artifacts saved: {artifacts}")

@pytest.fixture(scope="session")
def test_credentials() -> Dict[str, str]:
    """Load MS Rewards test credentials from environment."""
    creds = {
        "email": os.getenv("MS_REWARDS_E2E_EMAIL"),
        "password": os.getenv("MS_REWARDS_E2E_PASSWORD"),
        "totp_secret": os.getenv("MS_REWARDS_E2E_TOTP_SECRET")
    }
    if not creds["email"] or not creds["password"]:
        pytest.skip("Test credentials not set. Set MS_REWARDS_E2E_EMAIL and MS_REWARDS_E2E_PASSWORD")
    return creds


@pytest.fixture
async def admin_logged_in_page(page, test_credentials):
    """Perform full login flow and return authenticated page."""
    from tests.e2e.helpers.login import perform_login
    await perform_login(page, test_credentials)
    return page


@pytest.fixture
async def no_login_page(page: Page):
    """Ensure page is in no-login state; skip if login detected."""
    await page.goto("https://www.bing.com", wait_until="domcontentloaded")

    # Check if we're logged in - if so, optionally skip or logout
    signin_btn = await page.query_selector("a[href*='login'], button:has-text('Sign in')")
    profile_elem = await page.query_selector(".mee-avatar, [data-ct*='profile']")

    if profile_elem and not signin_btn:
        # Appears logged in - Option A: skip, Option B: logout
        # Preferred: skip to preserve test isolation
        pytest.skip("Test requires no-login state but page appears authenticated. Use --no-login context.")

    return page


@pytest.fixture
async def incognito_context(browser: Browser):
    """Fresh context without any storage state (guaranteed no-login)."""
    context = await browser.new_context()
    yield context
    await context.close()
