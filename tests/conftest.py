"""
Shared pytest configuration and fixtures for MS Rewards Automator tests.

This module provides:
- Hypothesis profile configuration
- Pytest hooks for test failure reporting
- Common fixtures for test isolation
"""

import logging
import os

import pytest
from hypothesis import Verbosity, settings

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ============================================================================
# Hypothesis Configuration
# ============================================================================

# Register hypothesis profiles for different test environments
settings.register_profile(
    "default",
    max_examples=100,
    deadline=5000,  # 5 seconds per test
    print_blob=True,
)

settings.register_profile(
    "ci",
    max_examples=200,
    deadline=10000,  # 10 seconds per test in CI
    print_blob=True,
)

settings.register_profile(
    "dev",
    max_examples=50,
    deadline=None,  # No deadline in development
    verbosity=Verbosity.verbose,
)

# Load profile based on environment variable
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)


# ============================================================================
# Pytest Hooks
# ============================================================================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test failures and add additional context.

    This hook runs after each test phase (setup, call, teardown) and
    adds useful debugging information to failure reports.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Add test arguments to failure report
        if hasattr(item, "funcargs"):
            report.sections.append(("Test Arguments", str(item.funcargs)))

        # Log failure for debugging
        logging.error(f"Test failed: {item.nodeid}")
        logging.error(f"Failure reason: {report.longreprtext}")


# ============================================================================
# Common Fixtures
# ============================================================================


@pytest.fixture
def temp_workspace(tmp_path):
    """
    Provide a temporary workspace directory for file operations.

    The directory is automatically cleaned up after the test.
    """
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    yield workspace
    # Cleanup handled by pytest tmp_path


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
def mock_config():
    """
    Provide a mock ConfigManager for testing.

    Returns a mock object with common configuration values.
    """
    from unittest.mock import MagicMock

    config = MagicMock()

    # Account settings
    config.get.side_effect = lambda key, default=None: {
        "account.storage_state_path": "test_storage_state.json",
        "account.login_url": "https://rewards.microsoft.com/",
        "login.state_machine_enabled": True,
        "login.max_transitions": 20,
        "login.transition_timeout": 300,
        "task_system.min_delay": 1,
        "task_system.max_delay": 2,
        "query_engine.enabled": True,
        "query_engine.cache_enabled": True,
    }.get(key, default)

    return config


@pytest.fixture
def mock_browser_context():
    """
    Provide a mock BrowserContext for testing.

    Returns a mock Playwright BrowserContext with common methods.
    """
    from unittest.mock import AsyncMock, MagicMock

    context = MagicMock()

    # Mock async methods
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    context.storage_state = AsyncMock(return_value={"cookies": [], "origins": []})

    return context


# ============================================================================
# Import Fixtures from Modules
# ============================================================================

# Import mock account fixtures
pytest_plugins = [
    "tests.fixtures.mock_accounts",
    "tests.fixtures.mock_dashboards",
]
