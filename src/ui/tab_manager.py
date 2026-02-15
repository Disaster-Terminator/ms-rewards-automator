"""
标签页管理器模块
处理新标签页的监听、关闭和导航优化
"""

import asyncio
import logging
from typing import Optional, Callable
from playwright.async_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

logger = logging.getLogger(__name__)


class TabManager:
    """标签页管理器类"""
    
    def __init__(self, context: BrowserContext):
        """
        初始化标签页管理器
        
        Args:
            context: 浏览器上下文
        """
        self.context = context
        self.new_page_handlers = []
        self.is_monitoring = False
        
    async def start_monitoring(self):
        """开始监听新标签页创建"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.context.on("page", self._handle_new_page)
        logger.debug("标签页监听已启动")
    
    async def stop_monitoring(self):
        """停止监听新标签页创建"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        # 移除事件监听器
        try:
            self.context.remove_listener("page", self._handle_new_page)
        except (PlaywrightError, RuntimeError):
            pass
        logger.debug("标签页监听已停止")
    
    def _handle_new_page(self, new_page: Page):
        """
        处理新创建的页面
        
        Args:
            new_page: 新创建的页面
        """
        logger.debug("检测到新标签页创建")
        
        # 异步处理新页面
        asyncio.create_task(self._process_new_page(new_page))
    
    async def _process_new_page(self, new_page: Page):
        """
        处理新页面的逻辑
        
        Args:
            new_page: 新创建的页面
        """
        try:
            # 立即注入防护脚本，防止 beforeunload 对话框
            try:
                await new_page.evaluate("""
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
                """)
                logger.debug("已为新页面注入防护脚本")
            except (PlaywrightTimeout, PlaywrightError) as e:
                logger.debug(f"注入防护脚本失败: {e}")
            
            # 等待页面稍微加载
            await asyncio.sleep(0.1)
            
            # 获取页面URL
            try:
                url = new_page.url
                logger.debug(f"新标签页URL: {url}")
            except (PlaywrightTimeout, PlaywrightError):
                url = "about:blank"
            
            # 如果是空白页面或者不需要的页面，直接关闭
            if url in ["about:blank", "", "chrome://newtab/"]:
                logger.debug("关闭空白新标签页")
                await self._safe_close_page(new_page)
                return
            
            # 等待一小段时间让stealth脚本完成
            await asyncio.sleep(0.5)
            
            # 关闭新标签页
            logger.debug("关闭新标签页")
            await self._safe_close_page(new_page)
            
        except (PlaywrightTimeout, PlaywrightError) as e:
            logger.debug(f"处理新标签页时出错: {e}")
            await self._safe_close_page(new_page)
    
    async def _safe_close_page(self, page: Page):
        """
        安全地关闭页面
        
        Args:
            page: 要关闭的页面
        """
        try:
            if not page.is_closed():
                # 在关闭前禁用 beforeunload 事件，防止"确定要离开？"对话框
                try:
                    await page.evaluate("""
                        () => {
                            // 移除所有 beforeunload 监听器
                            window.onbeforeunload = null;
                            
                            // 覆盖 addEventListener 以阻止新的 beforeunload 监听器
                            const originalAddEventListener = window.addEventListener;
                            window.addEventListener = function(type, listener, options) {
                                if (type === 'beforeunload') {
                                    return; // 忽略 beforeunload 监听器
                                }
                                return originalAddEventListener.call(this, type, listener, options);
                            };
                        }
                    """)
                    logger.debug("已禁用页面的 beforeunload 事件")
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.debug(f"禁用 beforeunload 事件失败: {e}")
                
                # 关闭页面
                await page.close()
                logger.debug("页面已关闭")
        except (PlaywrightTimeout, PlaywrightError) as e:
            logger.debug(f"关闭页面时出错: {e}")
    
    async def click_link_in_current_tab(
        self, 
        page: Page, 
        link_element, 
        timeout: int = 10000
    ) -> bool:
        """
        在当前标签页中点击链接，防止新标签页打开
        
        Args:
            page: 当前页面
            link_element: 链接元素
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        try:
            # 获取链接URL
            link_url = await link_element.get_attribute("href")
            if not link_url or link_url.startswith("javascript:") or link_url == "#":
                logger.debug("无效的链接URL，跳过")
                return False
            
            # 开始监听新标签页
            await self.start_monitoring()
            
            # 保存原始URL
            original_url = page.url
            
            # 方法1: 尝试修改链接的target属性
            try:
                await link_element.evaluate("el => el.removeAttribute('target')")
                await link_element.evaluate("el => el.setAttribute('target', '_self')")
            except (PlaywrightTimeout, PlaywrightError):
                pass
            
            # 方法2: 使用JavaScript点击而不是Playwright点击
            try:
                await link_element.evaluate("el => el.click()")
                
                # 等待导航或新标签页
                await asyncio.sleep(1)
                
                # 检查是否在当前页面导航了
                current_url = page.url
                if current_url != original_url:
                    logger.debug("链接在当前标签页中打开成功")
                    return True
                
            except (PlaywrightTimeout, PlaywrightError) as e:
                logger.debug(f"JavaScript点击失败: {e}")
            
            # 方法3: 直接导航到链接URL
            try:
                logger.debug(f"直接导航到: {link_url}")
                await page.goto(link_url, wait_until="domcontentloaded", timeout=timeout)
                return True
                
            except (PlaywrightTimeout, PlaywrightError) as e:
                logger.debug(f"直接导航失败: {e}")
                return False
            
        except (PlaywrightTimeout, PlaywrightError) as e:
            logger.debug(f"在当前标签页点击链接失败: {e}")
            return False
        
        finally:
            # 停止监听（延迟一点以确保处理完所有新标签页）
            await asyncio.sleep(1)
            await self.stop_monitoring()
    
    async def get_all_pages(self) -> list[Page]:
        """
        获取所有页面
        
        Returns:
            页面列表
        """
        return self.context.pages
    
    async def close_extra_pages(self, keep_page: Page):
        """
        关闭除指定页面外的所有页面
        
        Args:
            keep_page: 要保留的页面
        """
        try:
            all_pages = await self.get_all_pages()
            
            for page in all_pages:
                if page != keep_page and not page.is_closed():
                    try:
                        await page.close()
                        logger.debug("关闭额外页面")
                    except (PlaywrightTimeout, PlaywrightError):
                        pass
                        
        except (PlaywrightTimeout, PlaywrightError) as e:
            logger.debug(f"关闭额外页面时出错: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop_monitoring()