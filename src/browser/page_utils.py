"""
浏览器页面工具模块
提供临时页面的安全上下文管理
"""

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, Page

logger = logging.getLogger(__name__)

# 共享的 JavaScript 脚本常量
# 用于禁用页面的 beforeunload 事件，防止"确定要离开？"对话框
# 覆盖 confirm 和 alert 以静默处理弹窗
DISABLE_BEFORE_UNLOAD_SCRIPT = """
    () => {
        // 移除所有 beforeunload 监听器
        window.onbeforeunload = null;
        window.onunload = null;

        // 阻止新的 beforeunload 监听器
        const originalAddEventListener = window.addEventListener;
        window.addEventListener = function(type, listener, options) {
            if (type === 'beforeunload' || type === 'unload') {
                return;
            }
            return originalAddEventListener.call(this, type, listener, options);
        };

        // 覆盖 confirm 和 alert，防止弹窗
        window.confirm = () => true;
        window.alert = () => {};
    }
"""

# 用于禁用 beforeunload 事件并阻止 window.open
# 适用于需要完全控制新标签页的场景
DISABLE_BEFORE_UNLOAD_AND_WINDOW_OPEN_SCRIPT = """
    () => {
        // 禁用 beforeunload 事件
        window.onbeforeunload = null;

        // 阻止新的 beforeunload 监听器
        const originalAddEventListener = window.addEventListener;
        window.addEventListener = function(type, listener, options) {
            if (type === 'beforeunload') {
                console.log('[TabManager] Blocked beforeunload listener');
                return;
            }
            return originalAddEventListener.call(this, type, listener, options);
        };

        // 阻止 window.open
        window.open = function() {
            console.log('[TabManager] Blocked window.open()');
            return null;
        };
    }
"""


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
