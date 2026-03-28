import pytest
from playwright.async_api import Page

class TestConsentHandling:
    """Tests for cookie consent and privacy prompts in no-login mode."""

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_accept_cookies_button_clickable(self, page: Page):
        """If cookie banner appears, accept button should be clickable."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Look for cookie banner (region-dependent)
        consent_selectors = [
            "button#bnp_btn_accept",  # Microsoft consent
            "button:has-text('Accept')",
            "button:has-text('I agree')",
            "[role='dialog'] button"
        ]

        found = False
        for selector in consent_selectors:
            button = await page.query_selector(selector)
            if button and await button.is_visible():
                # Click and verify banner disappears
                await button.click()
                await page.wait_for_timeout(1000)
                # Banner should be gone or hidden
                banner = await page.query_selector(selector)
                if banner:
                    assert not await banner.is_visible(), "Cookie banner still visible after accept"
                found = True
                break
        
        if not found:
            pytest.skip("No visible cookie consent banner found (region may not show)")

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_search_works_without_accepting_cookies(self, page: Page):
        """Search should work even if user ignores cookie banner."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Don't interact with banner, just perform search
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        await search_box.fill("test")
        await page.keyboard.press("Enter")
        
        # Results should appear regardless of consent
        # Use attached state for resilience
        try:
            await page.wait_for_selector(".b_algo", timeout=10000, state="attached")
        except Exception:
            # Fallback to checking any result content
            await page.wait_for_selector("#b_results", timeout=5000, state="attached")

        results = await page.query_selector(".b_algo, .b_title, #b_results .b_algo")
        assert results is not None
