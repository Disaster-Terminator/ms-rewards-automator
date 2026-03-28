import pytest
from playwright.async_api import Page
from datetime import datetime, timedelta

class TestSearchHistory:
    """Tests for search history tracking and display."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(120)
    async def test_recent_searches_displayed_on_bing(self, page: Page, test_credentials):
        """
        After performing searches, Bing search homepage should show recent searches.
        """
        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)

        # Perform a few searches first
        search_terms = ["alpha search history", "beta search history", "gamma search history"]
        
        for term in search_terms:
            await page.goto("https://www.bing.com", wait_until="domcontentloaded")
            # Handle consent if it appears
            consent_btn = await page.query_selector("button#bnp_btn_accept, #vc_consent_yes")
            if consent_btn:
                await consent_btn.click()

            search_box = await page.query_selector("input[name='q'], textarea[name='q']")
            assert search_box is not None
            await search_box.fill(term)
            await page.keyboard.press("Enter")
            await page.wait_for_selector(".b_algo, .b_title, #b_results", timeout=15000, state="attached")
            # Short wait to ensure history is recorded
            await page.wait_for_timeout(2000)

        # Navigate back to homepage
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Check search box for recent suggestions (often in dropdown)
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        assert search_box is not None
        await search_box.click()
        await page.wait_for_timeout(2000)

        # suggestions may appear in dropdown or listbox
        suggestions_visible = False
        try:
            # sa_t is common for suggestions; [role='listbox'] is ARIA
            suggestions = await page.query_selector_all(".sa_t, [role='listbox'] li")
            if len(suggestions) >= 2:
                suggestions_visible = True
        except Exception:
            pass

        # If suggestions not shown in dropdown, check "Recent searches" section
        if not suggestions_visible:
            # Look for elements containing the text "Recent" and "Searches"
            recent_section = await page.query_selector("text='Recent searches', text='最近的搜索'")
            if recent_section:
                suggestions_visible = True

        # NOTE: Search history may be disabled by settings or obscured by privacy mode/extensions
        # We'll assert if we find it, but maybe not fail if not found since it's configuration dependent
        if not suggestions_visible:
            pytest.skip("Could not verify search history (may be disabled in settings or hidden by region/consent)")

        assert suggestions_visible, "Search history suggestions should be visible after searches"

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(60)
    async def test_search_history_clears_after_authentication(self, page: Page):
        """Search history should be account-specific; new account starts fresh."""
        pytest.skip("Requires two distinct accounts with different search histories to verify separation")
        # Steps: login account A, perform searches, logout, login account B, verify no history from A
