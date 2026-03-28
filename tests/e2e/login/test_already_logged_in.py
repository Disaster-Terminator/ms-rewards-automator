import pytest
from playwright.async_api import Page, BrowserContext

class TestAlreadyLoggedIn:
    """Tests for scenarios where user is already authenticated."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_navigate_to_rewards_when_already_logged_in(self, page: Page, test_credentials):
        """When already logged in, rewards.bing.com should show dashboard directly."""
        # Perform initial login
        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)

        # Navigate away, then back
        await page.goto("https://www.bing.com")
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")

        # Should see dashboard immediately (no login page redirect)
        await page.wait_for_selector(".progressContainer, [data-ct*='dashboard']", timeout=10000)
        url = page.url
        assert "rewards.bing.com" in url and "login" not in url.lower()

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_login_page_not_shown_when_authenticated(self, admin_logged_in_page: Page):
        """Authenticated session should not see login.live.com page."""
        # admin_logged_in_page fixture already performs login
        page = admin_logged_in_page
        
        # URL should not be a login page
        current_url = page.url
        assert "login.live.com" not in current_url
        assert "rewards.bing.com" in current_url
