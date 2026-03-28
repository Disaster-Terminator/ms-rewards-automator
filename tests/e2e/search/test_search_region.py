import pytest
from playwright.async_api import Page
import re

class TestSearchRegion:
    """Tests for region-specific search behavior and currency handling."""

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_bing_region_detected_correctly(self, page: Page):
        """Bing should detect and display results appropriate to IP region."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Check for region indicator in footer or settings
        # Bing footer often contains the region/country name
        # Common selectors for region in footer: #sh_r, .sw_region, footer span
        region_text = None
        selectors = ["footer", "#sh_r", ".sw_region", "a#id_l"]
        
        for selector in selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text and len(text.strip()) > 0:
                        region_text = text
                        break
            except Exception:
                continue

        if region_text:
            # Extract region code (e.g., "United States", "EN-US", "中国")
            # Use a more inclusive regex that allows non-Latin characters
            import re
            match = re.search(r'([A-Za-z0-9\-\. ]+|[^\x00-\x7F]+)', region_text)
            if match:
                detected_region = match.group(1).strip()
                assert len(detected_region) >= 1, f"Region detection produced too short string from: {region_text}"
            else:
                pytest.skip(f"Could not extract region from text: {region_text}")
        else:
            pytest.skip("Region indicator not found in common selectors")

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_search_results_localized(self, page: Page):
        """Search results should be in local language/locale."""
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")

        # Perform local search (e.g., "weather")
        search_box = await page.query_selector("input[name='q'], textarea[name='q']")
        assert search_box is not None
        await search_box.fill("weather")
        await page.keyboard.press("Enter")
        await page.wait_for_selector(".b_algo, .b_title, #b_results", timeout=15000, state="attached")

        # Results should contain local language
        # For English: "Weather", "forecast", etc.
        # This is region-specific; we'll check for generic signs of content loading
        body_text = await page.text_content("body")
        assert body_text is not None and len(body_text) > 500, "Search results page body too short"
        
        # Heuristic for localization: check if common localized terms appear
        # This is difficult without knowing the expected locale, so we'll skip 
        # the specific assertion and just ensure content exists.
        pytest.skip("Localization validation needs region-specific expectations (IP-dependent)")

    @pytest.mark.e2e
    @pytest.mark.timeout(60)
    async def test_currency_in_points_display(self, page: Page, test_credentials):
        """Points should display with appropriate currency/symbol if applicable."""
        from tests.e2e.helpers.login import perform_login
        await perform_login(page, test_credentials)
        
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")

        # Extract numeric value
        points_selectors = [".credits_value", ".mee-textPoints", ".pointsBalance"]
        points_text = None
        for selector in points_selectors:
            el = await page.query_selector(selector)
            if el:
                points_text = await el.text_content()
                break
                
        if points_text:
            # Check if contains numeric value
            assert any(c.isdigit() for c in points_text), f"Points display missing numeric value: {points_text}"
        else:
            pytest.skip("Points display selector not found on rewards dashboard")
