"""
测试 beforeunload 对话框修复
验证在保存会话状态和清理资源时不会被对话框阻塞
"""

import asyncio
import logging

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_beforeunload_fix():
    """测试 beforeunload 对话框的修复"""

    async with async_playwright() as p:
        # 创建浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # 添加对话框处理器
        context.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        # 创建主页面
        main_page = await context.new_page()
        await main_page.goto("https://www.bing.com")

        # 模拟创建一个带有 beforeunload 的新页面
        logger.info("创建带有 beforeunload 事件的新页面...")
        new_page = await context.new_page()
        await new_page.goto("https://www.bing.com")

        # 注入 beforeunload 事件
        await new_page.evaluate("""
            () => {
                window.onbeforeunload = function(e) {
                    e.preventDefault();
                    e.returnValue = '';
                    return '确定要离开？';
                };
            }
        """)

        logger.info("已注入 beforeunload 事件")

        # 测试1: 禁用 beforeunload 后关闭页面
        logger.info("\n测试1: 禁用 beforeunload 后关闭页面...")
        try:
            # 禁用 beforeunload
            await new_page.evaluate("""
                () => {
                    window.onbeforeunload = null;
                    window.addEventListener = function(type, listener, options) {
                        if (type === 'beforeunload') return;
                        return EventTarget.prototype.addEventListener.call(this, type, listener, options);
                    };
                }
            """)

            await new_page.close()
            logger.info("✓ 页面关闭成功，没有对话框")
        except Exception as e:
            logger.error(f"✗ 页面关闭失败: {e}")

        # 测试2: 创建另一个页面并测试 storage_state
        logger.info("\n测试2: 测试 storage_state 调用...")
        new_page2 = await context.new_page()
        await new_page2.goto("https://www.bing.com")

        # 注入 beforeunload
        await new_page2.evaluate("""
            () => {
                window.onbeforeunload = function(e) {
                    e.preventDefault();
                    e.returnValue = '';
                    return '确定要离开？';
                };
            }
        """)

        # 关闭额外页面
        logger.info("关闭额外页面...")
        for page in context.pages[1:]:
            try:
                if not page.is_closed():
                    # 禁用 beforeunload
                    await page.evaluate("""
                        () => {
                            window.onbeforeunload = null;
                        }
                    """)
                    await page.close()
                    logger.info("✓ 额外页面已关闭")
            except Exception as e:
                logger.error(f"✗ 关闭页面失败: {e}")

        # 调用 storage_state
        try:
            logger.info("调用 storage_state...")
            state = await context.storage_state()
            logger.info(
                f"✓ storage_state 调用成功，获取了 {len(state.get('cookies', []))} 个 cookies"
            )
        except Exception as e:
            logger.error(f"✗ storage_state 调用失败: {e}")

        # 清理
        await context.close()
        await browser.close()

        logger.info("\n✓ 所有测试完成")


if __name__ == "__main__":
    asyncio.run(test_beforeunload_fix())
