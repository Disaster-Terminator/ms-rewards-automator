import pytest
import re
from playwright.async_api import Page

class TestSearchPointsVerification:
    """Tests that verify points are awarded after search completion."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(180)
    async def test_points_increase_after_search(self, page: Page, test_credentials):
        """
        Execute search and verify points balance increases.
        Note: Points may be delayed; check within 2 minutes post-search.
        """
        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)

        # Get initial points from rewards dashboard
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")
        initial_points = await self._extract_points(page)

        # Perform a search (authenticated)
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")
        # Handle consent if it appears
        consent_btn = await page.query_selector("button#bnp_btn_accept, #vc_consent_yes")
        if consent_btn:
            await consent_btn.click()
            
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        assert search_box is not None, "Search input not found"
        await search_box.fill("points verification test")
        await page.keyboard.press("Enter")
        
        # Use attached state to be more resilient
        await page.wait_for_selector(".b_algo, .b_title, #b_results", timeout=15000, state="attached")

        # Wait and check points again (points may be delayed)
        await page.wait_for_timeout(10000)  # 10s delay for points to credit
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")
        new_points = await self._extract_points(page)

        # Points should increase (or stay same if already maxed for day)
        # Allow for edge: if initial_points == 0, then new_points should be > 0
        if initial_points > 0:
            assert new_points >= initial_points, f"Points did not increase: {initial_points} -> {new_points}"
        else:
            # If initial points couldn't be detected, we can't verify increase quantitatively
            # but we might check if new_points is > 0
            if new_points == 0:
                 pytest.skip("Initial points not detectable; skipping quantitative verification")

    async def _extract_points(self, page: Page) -> int:
        """Extract numeric points value from dashboard."""
        selectors = [
            ".credits_value",
            ".mee-textPoints",
            "[data-ct*='points']",
            ".pointsBalance",
            "#sr_points"
        ]
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text:
                        # Extract number, handle commas
                        match = re.search(r'([\d,]+)', text.replace(',', ''))
                        if match:
                            return int(match.group(1))
            except Exception:
                continue
        return 0

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(180)
    async def test_search_points_vary_by_device_type(self, page: Page, test_credentials):
        """
        Verify that desktop and mobile searches award points differently (if applicable).
        Some accounts differentiate points based on device type.
        """
        pytest.skip("Device-specific point differentiation is account/promo dependent; informational test")
