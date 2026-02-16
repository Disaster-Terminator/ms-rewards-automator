"""
Mock account fixtures for testing MS Rewards Automator.

Provides predefined test accounts and hypothesis strategies for generating
random accounts for property-based testing.
"""

from dataclasses import dataclass

import pytest
from hypothesis import strategies as st


@dataclass
class MockAccount:
    """Mock account for testing."""

    email: str
    password: str
    totp_secret: str | None = None
    account_type: str = "standard"  # standard, 2fa, passwordless


# ============================================================================
# Predefined Test Accounts
# ============================================================================

TEST_ACCOUNTS = {
    "standard": MockAccount(
        email="test@example.com",
        password="TestPassword123",
        totp_secret=None,
        account_type="standard",
    ),
    "2fa": MockAccount(
        email="test2fa@example.com",
        password="TestPassword123",
        totp_secret="JBSWY3DPEHPK3PXP",  # Base32 encoded secret
        account_type="2fa",
    ),
    "passwordless": MockAccount(
        email="testpwdless@example.com", password="", totp_secret=None, account_type="passwordless"
    ),
}


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating random mock accounts
mock_account_strategy = st.builds(
    MockAccount,
    email=st.emails(),
    password=st.text(
        min_size=8,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),  # Uppercase, lowercase, digits
            min_codepoint=33,
            max_codepoint=126,  # Printable ASCII
        ),
    ),
    totp_secret=st.one_of(
        st.none(), st.text(min_size=16, max_size=16, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    ),
    account_type=st.sampled_from(["standard", "2fa", "passwordless"]),
)


# ============================================================================
# Pytest Fixtures
# ============================================================================


@pytest.fixture
def mock_account_standard():
    """Provide a standard mock account."""
    return TEST_ACCOUNTS["standard"]


@pytest.fixture
def mock_account_2fa():
    """Provide a 2FA-enabled mock account."""
    return TEST_ACCOUNTS["2fa"]


@pytest.fixture
def mock_account_passwordless():
    """Provide a passwordless mock account."""
    return TEST_ACCOUNTS["passwordless"]


@pytest.fixture(params=["standard", "2fa", "passwordless"])
def mock_account_all_types(request):
    """Parametrized fixture that provides all account types."""
    return TEST_ACCOUNTS[request.param]
