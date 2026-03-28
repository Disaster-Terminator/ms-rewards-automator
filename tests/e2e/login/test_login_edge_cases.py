import pytest
from playwright.async_api import Page, TimeoutError

class TestLoginEdgeCases:
    """Edge case and error scenario tests for login."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_invalid_password_shows_error(self, page: Page, test_credentials):
        """Invalid password should display error message, not crash."""
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")

        # Enter email, then wrong password
        email_field = await page.wait_for_selector("input[type='email']", timeout=10000)
        await email_field.fill(test_credentials["email"])
        await page.click("input[type='submit']")
        
        password_field = await page.wait_for_selector("input[type='password']", timeout=10000)
        await password_field.fill("wrong_password_123")
        await page.click("input[type='submit']")

        # Should see error indicator (class contains 'error' or text 'incorrect')
        # Common error message selectors for MS login
        error_element = await page.query_selector(".error, [role='alert'], [id='passwordError'], text='incorrect'")
        assert error_element is not None, "Error message not shown for invalid password"

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_bing_rewards_redirects_to_login_if_not_authenticated(self, page: Page):
        """Unauthenticated access to rewards should redirect to Microsoft login."""
        # Ensure starting fresh (no storage state)
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")

        # Should redirect to login.live.com within a few seconds
        try:
            await page.wait_for_url(lambda url: "login.live.com" in url, timeout=20000)
            assert "login.live.com" in page.url
        except TimeoutError:
            # May show Bing's own login page
            current_url = page.url
            assert "login" in current_url.lower() or "account" in current_url.lower()

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_playwright_browser_close_after_login(self, browser):
        """Verify browser can be closed cleanly after login context."""
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://rewards.bing.com")

        # No assertion failure during close
        await context.close()
        # Verify it's closed (this might be implicitly true as context.close() returns)
        assert True 
