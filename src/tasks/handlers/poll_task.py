"""
Poll Task Handler

Handles poll tasks where the user needs to select an option and submit.
"""

import asyncio
import logging
import random

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from tasks.task_base import Task, TaskMetadata


class PollTask(Task):
    """Handler for poll tasks"""

    def __init__(self, metadata: TaskMetadata):
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)

    async def execute(self, page: Page) -> bool:
        """
        Execute poll task

        Args:
            page: Playwright page object

        Returns:
            True if task completed successfully, False otherwise
        """
        self.logger.info(f"Executing poll task: {self.metadata.title}")

        if not self.metadata.destination_url:
            self.logger.error("No destination URL provided")
            return False

        try:
            # Navigate to the poll
            self.logger.debug(f"Navigating to: {self.metadata.destination_url}")
            await page.goto(self.metadata.destination_url, wait_until="networkidle", timeout=30000)

            # Wait for poll to load
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # Select a poll option
            option_selected = await self._select_poll_option(page)

            if not option_selected:
                self.logger.warning("Failed to select poll option")
                return False

            # Submit the poll
            submitted = await self._submit_poll(page)

            if submitted:
                self.logger.info("Poll submitted successfully")
                return True
            else:
                self.logger.warning("Failed to submit poll")
                return False

        except PlaywrightTimeout:
            self.logger.error("Timeout while loading poll")
            return False
        except Exception as e:
            self.logger.error(f"Error executing poll task: {e}")
            return False

    async def _select_poll_option(self, page: Page) -> bool:
        """
        Select a random poll option

        Args:
            page: Playwright page object

        Returns:
            True if option was selected, False otherwise
        """
        try:
            # Common selectors for poll options
            option_selectors = [
                'input[type="radio"]',
                ".poll-option",
                '[class*="poll-choice"]',
                'button[class*="option"]',
            ]

            for selector in option_selectors:
                options = await page.query_selector_all(selector)
                if options and len(options) > 0:
                    # Select a random option
                    selected_option = random.choice(options)
                    await selected_option.click()
                    self.logger.debug(f"Selected poll option using selector: {selector}")
                    await asyncio.sleep(1)
                    return True

            self.logger.warning("No poll options found")
            return False

        except Exception as e:
            self.logger.error(f"Error selecting poll option: {e}")
            return False

    async def _submit_poll(self, page: Page) -> bool:
        """
        Submit the poll

        Args:
            page: Playwright page object

        Returns:
            True if poll was submitted, False otherwise
        """
        try:
            # Common selectors for submit buttons
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Vote")',
                '[class*="submit-button"]',
            ]

            for selector in submit_selectors:
                try:
                    submit_button = await page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if submit_button:
                        await submit_button.click()
                        self.logger.debug(f"Clicked submit button: {selector}")
                        await asyncio.sleep(2)
                        return True
                except PlaywrightTimeout:
                    continue

            # If no submit button found, the poll might auto-submit
            self.logger.debug("No submit button found, assuming auto-submit")
            return True

        except Exception as e:
            self.logger.error(f"Error submitting poll: {e}")
            return False
