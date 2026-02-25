"""
浏览器页面工具模块
提供临时页面的安全上下文管理
"""

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, Page

logger = logging.getLogger(__name__)


@asynccontextmanager
async def temp_page(context: BrowserContext):
    """
    临时页面上下文管理器，确保页面资源正确释放

    Args:
        context: Playwright BrowserContext 对象

    Yields:
        Page: 新创建的页面对象

    Example:
        async with temp_page(page.context) as temp:
            result = await temp.evaluate("() => document.title")
    """
    page: Page | None = None
    try:
        page = await context.new_page()
        yield page
    except Exception as e:
        logger.debug(f"临时页面操作异常: {e}")
        raise
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception as close_error:
                logger.debug(f"关闭临时页面失败: {close_error}")


@asynccontextmanager
async def safe_temp_page(
    context: BrowserContext, on_error: Callable[[Exception], None] | None = None
):
    """
    安全的临时页面上下文管理器，页面创建失败时返回None

    Args:
        context: Playwright BrowserContext 对象
        on_error: 异常回调函数，接收Exception参数

    Yields:
        Page | None: 新创建的页面对象，创建失败时为None
    """
    page: Page | None = None
    try:
        page = await context.new_page()
    except Exception as e:
        logger.warning(f"创建临时页面失败: {e}")
        if on_error:
            on_error(e)
        yield None
        return

    try:
        yield page
    finally:
        if page is not None:
            try:
                await page.close()
            except Exception as close_error:
                logger.debug(f"关闭临时页面失败: {close_error}")
