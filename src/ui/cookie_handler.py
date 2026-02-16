"""
Cookie 弹窗处理模块
处理网站的 Cookie 同意弹窗
"""

import asyncio
import logging

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CookieHandler:
    """Cookie 弹窗处理器"""

    # Cookie 同意按钮选择器
    ACCEPT_SELECTORS = [
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
        "button:has-text('I accept')",
        "button:has-text('I agree')",
        "button:has-text('同意')",
        "button:has-text('接受')",
        "button#accept-cookie-notification",
        "button[id*='accept']",
        "button[id*='cookie']",
        "a:has-text('Accept')",
        "#cookie-banner button",
        ".cookie-banner button",
        "[class*='cookie'] button",
    ]

    @staticmethod
    async def handle_cookie_popup(page: Page, timeout: int = 3000) -> bool:
        """
        处理 Cookie 弹窗

        Args:
            page: Playwright Page 对象
            timeout: 超时时间（毫秒）

        Returns:
            是否找到并处理了弹窗
        """
        try:
            logger.debug("检查 Cookie 弹窗...")

            # 等待一下让弹窗出现
            await asyncio.sleep(0.5)

            # 尝试所有可能的选择器（使用更短的超时）
            for selector in CookieHandler.ACCEPT_SELECTORS:
                try:
                    button = await page.wait_for_selector(selector, timeout=1000, state="visible")

                    if button:
                        logger.info(f"找到 Cookie 同意按钮: {selector}")

                        # 点击按钮
                        await button.click()

                        # 等待弹窗消失
                        await asyncio.sleep(0.5)

                        logger.info("✓ Cookie 弹窗已处理")
                        return True

                except Exception:
                    # 静默失败，继续尝试下一个选择器
                    continue

            logger.debug("未找到 Cookie 弹窗")
            return False

        except Exception as e:
            logger.debug(f"处理 Cookie 弹窗时出错: {e}")
            return False

    @staticmethod
    async def auto_handle_popups(page: Page):
        """
        自动处理页面上的弹窗

        Args:
            page: Playwright Page 对象
        """
        try:
            # 处理 Cookie 弹窗
            await CookieHandler.handle_cookie_popup(page)

            # 可以添加其他弹窗处理
            # 例如：通知弹窗、广告弹窗等

        except Exception as e:
            logger.debug(f"自动处理弹窗时出错: {e}")
