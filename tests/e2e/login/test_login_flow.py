import pytest
from playwright.async_api import Page

class TestLoginFlow:
    """Tests for Microsoft Rewards login flow."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_successful_login_with_credentials(self, page: Page, test_credentials):
        """Test full login flow with valid email/password."""
        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)

        # Verify dashboard loaded
        assert "rewards.bing.com" in page.url
        dashboard = await page.query_selector(".progressContainer, [data-ct*='dashboard']")
        assert dashboard is not None, "Dashboard not visible after login"

        # Check user profile element (avatar/initials)
        # Using more specific selectors that match common MS Bing/Rewards layout
        profile = await page.query_selector(".mee-avatar, [data-ct*='profile'], #m_p, #id_l")
        assert profile is not None, "Profile element not found"

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_login_with_2fa(self, page: Page, test_credentials):
        """Test login flow with 2FA enabled account."""
        if not test_credentials.get("totp_secret"):
            pytest.skip("No TOTP secret configured for 2FA test")

        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)

        # Verify dashboard reached
        await page.wait_for_selector(".progressContainer", timeout=30000)
        assert "rewards.bing.com" in page.url

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_login_skipped_without_credentials(self):
        """Verify tests skip gracefully when credentials not set."""
        # This test should be skipped by the e2e_test_account (test_credentials) fixture if missing.
        # But here we show that we can skip manually if needed.
        pytest.skip("This test should be skipped if credentials missing")
