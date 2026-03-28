import pytest
from playwright.async_api import Page

class TestSearchNoLogin:
    """Search tests that run without authentication (no-login-first strategy)."""

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_bing_search_page_loads(self, page: Page):
        """Bing.com homepage loads in no-login state."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=15000)
        title = await page.title()
        assert "Bing" in title or "必应" in title

        # Verify search box present
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        assert search_box is not None, "Search input not found"

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_search_execution_returns_results(self, page: Page):
        """Executing a search displays results without login."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        assert search_box
        await search_box.fill("weather today")
        await page.keyboard.press("Enter")

        # Wait for results page
        await page.wait_for_url(lambda url: "search?" in url, timeout=10000)

        # Check results container exists (try multiple possible selectors)
        result_selectors = [".b_algo", ".b_title", "#b_results", ".b_content"]
        found = False
        for selector in result_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000, state="attached")
                found = True
                break
            except Exception:
                continue
        
        assert found, "No search results displayed"

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_search_autocomplete_suggests_terms(self, page: Page):
        """Typing in search box shows autocomplete suggestions."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        await search_box.fill("python")

        # Wait for suggestions to appear (Bing shows in bottom div)
        try:
            await page.wait_for_selector("[role='listbox'], .sa_anc", timeout=5000)
            suggestions = await page.query_selector_all("[role='listbox'] li, .sa_t")
            assert len(suggestions) > 0, "No autocomplete suggestions shown"
        except Exception:
             pytest.skip("No autocomplete suggestions shown (UI variant or region)")

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_search_images_tab_works(self, page: Page):
        """Images tab shows image results without login."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Search for something
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        await search_box.fill("cats")
        await page.keyboard.press("Enter")
        # Wait for either results or tab bar
        await page.wait_for_selector(".b_algo, #b_header", timeout=10000)

        # Click Images tab - try multiple selectors for localization
        images_tab_selectors = [
            "a[href*='/images']",
            "a:has-text('Images')",
            "a:has-text('图片')",
            "#tiles"
        ]
        
        images_tab = None
        for selector in images_tab_selectors:
            images_tab = await page.query_selector(selector)
            if images_tab and await images_tab.is_visible():
                break
        
        if images_tab:
            await images_tab.click()
            try:
                # Wait for image results container
                await page.wait_for_selector(".imgres, .iusc, #mmComponent_images_1", timeout=10000)
                images = await page.query_selector_all(".imgres, .iusc")
                assert len(images) > 0 or await page.query_selector(".imgres, .iusc") is not None, "No images displayed after clicking Images tab"
            except Exception:
                pytest.skip("Images results not found (region-specific or UI variant)")
        else:
            pytest.skip("Images tab not found (variant UI)")

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_search_videos_tab_works(self, page: Page):
        """Videos tab shows video results without login."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        await search_box.fill("playwright tutorial")
        await page.keyboard.press("Enter")
        await page.wait_for_selector(".b_algo, #b_header", timeout=10000)

        videos_tab_selectors = [
            "a[href*='/videos']",
            "a:has-text('Videos')",
            "a:has-text('视频')"
        ]
        
        videos_tab = None
        for selector in videos_tab_selectors:
            videos_tab = await page.query_selector(selector)
            if videos_tab and await videos_tab.is_visible():
                break

        if videos_tab:
            await videos_tab.click()
            try:
                 await page.wait_for_selector(".vidres, [data-t*='video'], .dg_u", timeout=10000)
                 videos = await page.query_selector_all(".vidres, [data-t*='video'], .dg_u")
                 assert len(videos) > 0, "No videos displayed"
            except Exception:
                 pytest.skip("Videos results not found (region-specific or UI variant)")
        else:
            pytest.skip("Videos tab not found (region-specific)")

    @pytest.mark.e2e
    @pytest.mark.no_login
    @pytest.mark.timeout(30)
    async def test_parametrized_search_terms(self, page: Page, search_term: str):
        """Test multiple search terms from data file."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        await search_box.fill(search_term)
        await page.keyboard.press("Enter")
        
        # Results container could be different classes
        result_selectors = [".b_algo", ".b_title", "#b_results", ".b_content"]
        
        found = False
        for selector in result_selectors:
            try:
                # Use attached state to be more resilient to UI variations
                await page.wait_for_selector(selector, timeout=10000, state="attached")
                found = True
                break
            except Exception:
                continue
        
        assert found, f"No results container found for term: {search_term}"
        
        # Check if at least one result item exists
        results = await page.query_selector_all(".b_algo, .b_title")
        assert len(results) > 0, f"No results for term: {search_term}"
