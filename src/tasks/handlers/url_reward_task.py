"""
URL Reward Task Handler

Handles simple URL-based reward tasks where the user needs to visit a URL
and interact with the page to earn points.
"""

import asyncio
import logging
import random

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from tasks.task_base import Task, TaskMetadata


class UrlRewardTask(Task):
    """Handler for URL reward tasks"""

    def __init__(self, metadata: TaskMetadata):
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)

    async def execute(self, page: Page) -> bool:
        """
        Execute URL reward task

        Args:
            page: Playwright page object

        Returns:
            True if task completed successfully, False otherwise
        """
        self.logger.info(f"🔗 执行URL奖励任务: {self.metadata.title}")

        if not self.metadata.destination_url:
            self.logger.error("❌ 未提供目标URL")
            return False

        url = self.metadata.destination_url.strip()

        if not url or url == "None" or url == "null":
            self.logger.warning("⏭️  跳过空URL")
            return False

        if url.startswith(
            ("microsoft-edge://", "ms-windows-store://", "ms-settings://", "edge://")
        ):
            self.logger.warning(f"⏭️  跳过特殊协议URL: {url}")
            return False

        if not url.startswith(("http://", "https://")):
            self.logger.warning(f"⏭️  跳过无效协议URL: {url}")
            return False

        try:
            self.logger.debug(f"🌐 导航到: {url}")

            await page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )

            await page.wait_for_load_state("domcontentloaded")

            await asyncio.sleep(random.uniform(2, 4))

            final_url = page.url.lower()

            if (
                self.metadata.task_type in ("quiz", "poll")
                or "quiz" in final_url
                or "poll" in final_url
            ):
                success = await self._handle_quiz_task(page)
            elif "bing.com/search" in final_url:
                success = await self._handle_search_task(page)
            elif "puzzle" in final_url or "spotlight" in final_url:
                success = await self._handle_puzzle_task(page)
            else:
                success = await self._handle_generic_task(page)

            return success

        except PlaywrightTimeout:
            self.logger.error("❌ 加载页面超时")
            return False
        except Exception as e:
            self.logger.error(f"❌ 执行URL任务出错: {e}")
            return False

    async def _handle_search_task(self, page: Page) -> bool:
        """Handle search-based tasks"""
        self.logger.debug("  处理搜索任务...")

        await self._scroll_page(page)

        search_input = page.locator('input[type="search"], input[name="q"], #sb_form_q')
        if await search_input.count() > 0:
            await asyncio.sleep(random.uniform(1, 2))

        return True

    async def _handle_quiz_task(self, page: Page) -> bool:
        """Handle quiz/poll tasks"""
        self.logger.debug("  处理Quiz/Poll任务...")

        await self._scroll_page(page)

        start_button = page.locator(
            'button:has-text("Start"), button:has-text("开始"), a:has-text("Start")'
        )
        if await start_button.count() > 0:
            await start_button.first.click()
            await asyncio.sleep(random.uniform(2, 3))

        return True

    async def _handle_puzzle_task(self, page: Page) -> bool:
        """Handle puzzle tasks"""
        self.logger.debug("  处理拼图任务...")

        await self._scroll_page(page)
        await asyncio.sleep(random.uniform(3, 5))
        return True

    async def _handle_generic_task(self, page: Page) -> bool:
        """Handle generic URL tasks"""
        self.logger.debug("  处理通用任务...")

        await self._scroll_page(page)
        return True

    async def _scroll_page(self, page: Page):
        """Scroll the page to simulate human behavior"""
        try:
            for _ in range(random.randint(2, 4)):
                scroll_amount = random.randint(200, 500)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.5, 1.5))

            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
        except Exception:
            pass
