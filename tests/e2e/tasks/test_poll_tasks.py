import pytest
from playwright.async_api import Page

class TestPollTasks:
    """Tests for poll-type reward tasks (single-choice vote)."""

    @pytest.mark.e2e
    @pytest.mark.requires_login
    @pytest.mark.timeout(180)
    async def test_poll_task_completion(self, page: Page, task_discovery):
        """
        Find and complete a poll task if available.
        Polls typically present a single question with multiple choices.
        """
        # Ensure we are logged in before starting
        tasks = await task_discovery()
        # Find tasks that look like polls
        poll_tasks = [t for t in tasks if t.status == "available" and any(keyword in t.title.lower() for keyword in ["poll", "survey", "vote", "daily poll"])]

        if not poll_tasks:
            pytest.skip("No poll tasks available for this account/region")

        task = poll_tasks[0]
        # Poll tasks often open in a new tab, but we'll go directly to the URL
        await page.goto(task.url, wait_until="domcontentloaded", timeout=30000)

        # Poll flow: choose an option, then optionally click vote/submit
        # Look for poll options - often radio buttons or cards
        try:
            # Common selectors for poll questions and options
            await page.wait_for_selector(".poll-option, .btOptionCard, input[type='radio'], .poll-vote", timeout=10000)
        except:
            # Maybe already completed or different structure
            pass

        # Select an available poll option
        option = await page.query_selector(".btOptionCard, input[type='radio']:not(:checked), .poll-option")
        if option:
            await option.click()
            await page.wait_for_timeout(2000) # Wait for auto-advance or button to appear
            
            # Some polls require clicking "Vote" or "Submit"
            vote_btn = await page.query_selector("button:has-text('Vote'), button:has-text('Submit'), input[value='Vote'], .poll-submit")
            if vote_btn:
                await vote_btn.click()
                await page.wait_for_timeout(3000)
        
        # Check for completion - check if points were awarded or message shown
        completion_indicators = [
            "text='Thank you'",
            "text='You've earned'",
            "text='completed'",
            "text='Done'",
            ".poll-complete",
            ".poll-results",
            ".points-animation"
        ]
        
        found_indicator = False
        for indicator in completion_indicators:
            if await page.query_selector(indicator):
                found_indicator = True
                break

        # A poll is also considered complete if the results are shown
        results_view = await page.query_selector(".poll-results, .bt_pollResults")
        assert found_indicator or results_view is not None, f"Poll task '{task.title}' did not appear to complete"
