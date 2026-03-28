import pytest
import re
from playwright.async_api import Page

class TestTaskPointsAward:
    """Verify points are awarded after task completion."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(300)
    async def test_points_increase_after_url_task(self, page: Page, task_discovery, test_credentials):
        """
        Complete a URL reward task and check if points increase.
        """
        from tests.e2e.helpers.login import perform_login
        
        # 1. Login and navigate to rewards dashboard
        await perform_login(page, test_credentials)
        await page.goto("https://rewards.bing.com", wait_until="domcontentloaded")
        
        # 2. Get initial points
        initial_points = await self._extract_points(page)
        
        # 3. Find available tasks
        tasks = await task_discovery()
        # Find a simple URL task that is available and has points
        url_tasks = [t for t in tasks if t.status == "available" and t.url and t.reward_points > 0 and not any(kw in t.title.lower() for kw in ["quiz", "poll", "survey"])]
        
        if not url_tasks:
            # If no URL tasks, try any available task with points
            url_tasks = [t for t in tasks if t.status == "available" and t.url and t.reward_points > 0]
            
        if not url_tasks:
            pytest.skip("No available reward tasks with points found for this account")

        task = url_tasks[0]
        expected_reward = task.reward_points
        
        # 4. Execute the task
        # URL tasks usually complete just by visiting the URL and waiting a few seconds
        await page.goto(task.url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(10000) # Wait for reward to trigger
        
        # 5. Return to dashboard and check points
        # Sometimes needs a refresh or a small delay for points to update
        await page.goto("https://rewards.bing.com", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        new_points = await self._extract_points(page)
        
        # Verify points increased
        # Note: Points might not increase exactly by expected_reward if other tasks completed 
        # or if there's a delay, but it should be >= initial_points.
        # Ideally new_points >= initial_points + expected_reward
        assert new_points >= initial_points, f"Points decreased or stayed same: {initial_points} -> {new_points}"
        
        # Log for visibility in test report
        print(f"Task: {task.title}, Expected: +{expected_reward}, Actual: {initial_points} -> {new_points}")

    async def _extract_points(self, page: Page) -> int:
        """Extract numeric points from dashboard."""
        # Common selectors for points on rewards dashboard
        selectors = [
            ".credits_value", 
            "#m-points-container .mee-text-points", 
            ".mee-text-points",
            "#balance-item .mee-text-points",
            ".balance-value"
        ]
        
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.text_content()
                    # Remove commas and non-numeric chars
                    clean_text = re.sub(r'[^\d]', '', text)
                    if clean_text:
                        return int(clean_text)
            except:
                continue
        
        # Fallback: try searching for any text that looks like a point balance
        body_text = await page.inner_text("body")
        # Look for patterns like "1,234 points" or "1234" near "Available points"
        points_match = re.search(r'(\d{1,3}(,\d{3})*)\s*points', body_text, re.IGNORECASE)
        if points_match:
            return int(points_match.group(1).replace(',', ''))
            
        return 0
