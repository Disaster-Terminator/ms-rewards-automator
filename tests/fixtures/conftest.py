"""
Pytest configuration for fixtures.

This file makes fixtures available to all tests by importing them.
"""

# Import all fixtures to make them available
from tests.fixtures.mock_accounts import (
    mock_account_2fa,
    mock_account_all_types,
    mock_account_passwordless,
    mock_account_standard,
)
from tests.fixtures.mock_dashboards import (
    mock_dashboard_empty,
    mock_dashboard_full,
    mock_dashboard_generator,
    mock_dashboard_simple,
)

__all__ = [
    "mock_account_standard",
    "mock_account_2fa",
    "mock_account_passwordless",
    "mock_account_all_types",
    "mock_dashboard_empty",
    "mock_dashboard_simple",
    "mock_dashboard_full",
    "mock_dashboard_generator",
]
