"""
URL Reward Task Handler

Handles simple URL-based reward tasks where the user just needs to visit a URL
and wait for completion detection.
"""

import asyncio
import logging

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

        # Validate URL
        if not url or url == "None" or url == "null":
            self.logger.warning("⏭️  跳过空URL")
            return False

        # Skip special protocol URLs (microsoft-edge://, ms-windows-store://, etc.)
        if url.startswith(
            ("microsoft-edge://", "ms-windows-store://", "ms-settings://", "edge://")
        ):
            self.logger.warning(f"⏭️  跳过特殊协议URL: {url}")
            return False

        # Ensure URL has a valid protocol
        if not url.startswith(("http://", "https://")):
            self.logger.warning(f"⏭️  跳过无效协议URL: {url}")
            return False

        try:
            # Log navigation
            self.logger.debug(f"🌐 导航到: {url}")

            # Navigate to the task URL - 使用更宽松的等待策略
            await page.goto(
                self.metadata.destination_url,
                wait_until="domcontentloaded",  # 只等待DOM加载，不等待网络空闲
                timeout=15000,  # 减少超时时间到15秒
            )

            # 简单等待1秒让页面稳定
            await asyncio.sleep(1)

            self.logger.info(f"✅ 页面已加载: {page.url}")

            # URL任务通常是点击即完成，不需要复杂的完成检测
            # 只要页面成功加载就认为任务完成
            return True

        except PlaywrightTimeout:
            self.logger.error("❌ 加载页面超时")
            return False
        except Exception as e:
            self.logger.error(f"❌ 执行URL任务出错: {e}")
            return False
