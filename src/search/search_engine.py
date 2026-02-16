"""
搜索引擎模块
执行搜索任务，协调各个组件
"""

import asyncio
import logging
import random
import time

from playwright.async_api import Page

from browser.element_detector import ElementDetector
from ui.bing_theme_manager import BingThemeManager
from ui.cookie_handler import CookieHandler
from ui.tab_manager import TabManager

logger = logging.getLogger(__name__)


class SearchEngine:
    """搜索引擎类"""

    BING_URL = "https://www.bing.com"

    def __init__(self, config, term_generator, anti_ban, monitor=None, query_engine=None):
        """
        初始化搜索引擎

        Args:
            config: ConfigManager 实例
            term_generator: SearchTermGenerator 实例
            anti_ban: AntiBanModule 实例
            monitor: StateMonitor 实例（可选）
            query_engine: QueryEngine 实例（可选，用于智能查询生成）
        """
        self.config = config
        self.term_generator = term_generator
        self.anti_ban = anti_ban
        self.monitor = monitor
        self.query_engine = query_engine

        self.element_detector = ElementDetector(config)
        self.theme_manager = BingThemeManager(config)
        self._query_cache = []

        logger.info("搜索引擎初始化完成")

    async def navigate_to_bing(self, page: Page) -> bool:
        """导航到 Bing 搜索页面"""
        try:
            logger.debug(f"导航到 Bing: {self.BING_URL}")
            await page.goto(self.BING_URL, wait_until="networkidle", timeout=30000)
            return True
        except Exception as e:
            logger.error(f"导航到 Bing 失败: {e}")
            return False

    async def _get_search_term(self) -> str:
        """获取搜索词（支持 QueryEngine 或传统生成器）"""
        if self.query_engine and self.config.get("query_engine.enabled", False):
            if not self._query_cache:
                try:
                    count = max(
                        self.config.get("search.desktop_count", 30),
                        self.config.get("search.mobile_count", 20),
                    )
                    self._query_cache = await self.query_engine.generate_queries(count)
                    logger.debug(f"预生成了 {len(self._query_cache)} 个查询")
                except Exception as e:
                    logger.error(f"QueryEngine 生成查询失败，回退到传统生成器: {e}")
                    return self.term_generator.get_random_term()

            if self._query_cache:
                term = self._query_cache.pop(0)
                logger.debug(f"从 QueryEngine 获取查询: {term}")
                return term

        return self.term_generator.get_random_term()

    async def perform_single_search(self, page: Page, term: str, health_monitor=None) -> bool:
        """执行单次搜索"""
        try:
            logger.info(f"搜索: {term}")

            await self.element_detector.wait_for_page_ready(page, timeout=15000, check_network=True)

            page_errors = await self.element_detector.detect_page_errors(page)
            if page_errors:
                logger.warning(f"检测到页面错误: {page_errors}")

            if self.theme_manager.enabled:
                context = page.context
                await self.theme_manager.ensure_theme_before_search(page, context)

            current_url = page.url
            need_navigate = False

            if "rewards" in current_url:
                logger.debug("当前在 rewards 页面，需要导航到 Bing")
                need_navigate = True
            elif "bing.com" not in current_url:
                logger.debug("不在 Bing 页面，需要导航")
                need_navigate = True
            else:
                logger.debug(f"已在 Bing 页面: {current_url}")

            if need_navigate:
                try:
                    await page.goto(self.BING_URL, wait_until="domcontentloaded", timeout=20000)
                    await self.element_detector.wait_for_page_ready(page, timeout=10000)
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"导航到 Bing 失败: {e}")
                    return False

            try:
                handled = await CookieHandler.handle_cookie_popup(page)
                if handled:
                    await asyncio.sleep(1)
                    if "rewards" in page.url:
                        await page.goto(self.BING_URL, wait_until="domcontentloaded", timeout=20000)
                        await self.element_detector.wait_for_page_ready(page, timeout=10000)
                        await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"处理 Cookie 弹窗时出错: {e}")

            logger.debug(f"当前页面 URL: {page.url}")
            logger.debug(f"当前页面标题: {await page.title()}")

            search_box = await self.element_detector.find_search_box(page, timeout=10000)

            if not search_box:
                logger.error("未找到搜索框")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"search_box_not_found_{term[:20]}.png"
                )

                errors = await self.element_detector.detect_page_errors(page)
                if errors:
                    logger.error(f"页面错误: {errors}")

                logger.error(f"当前 URL: {page.url}")
                logger.error(f"当前标题: {await page.title()}")
                return False

            logger.info(f"✓ 找到搜索框，准备输入: {term}")

            try:
                logger.debug("准备输入搜索词...")

                try:
                    logger.debug("尝试方法1: fill()")
                    await search_box.fill("")
                    await asyncio.sleep(0.3)
                    await search_box.fill(term)
                    await asyncio.sleep(0.5)

                    input_value = await search_box.input_value()
                    if input_value == term:
                        logger.info(f"✓ 方法1成功输入: {term}")
                    else:
                        logger.warning(f"方法1输入验证失败: 期望'{term}', 实际'{input_value}'")
                        raise Exception("fill方法输入验证失败")

                except Exception as e1:
                    logger.debug(f"方法1失败: {e1}")

                    try:
                        logger.debug("尝试方法2: click + type()")
                        await search_box.click()
                        await asyncio.sleep(0.3)

                        await page.keyboard.press("Control+A")
                        await asyncio.sleep(0.1)
                        await page.keyboard.press("Backspace")
                        await asyncio.sleep(0.3)

                        await page.keyboard.type(term, delay=50)
                        await asyncio.sleep(0.5)

                        input_value = await search_box.input_value()
                        if input_value == term:
                            logger.info(f"✓ 方法2成功输入: {term}")
                        else:
                            logger.warning(f"方法2输入验证失败: 期望'{term}', 实际'{input_value}'")
                            raise Exception("type方法输入验证失败")

                    except Exception as e2:
                        logger.debug(f"方法2失败: {e2}")

                        try:
                            logger.debug("尝试方法3: JavaScript setValue")
                            await search_box.evaluate(f"el => el.value = '{term}'")
                            await asyncio.sleep(0.3)

                            await search_box.evaluate("""
                                el => {
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            """)
                            await asyncio.sleep(0.5)

                            input_value = await search_box.input_value()
                            if input_value == term:
                                logger.info(f"✓ 方法3成功输入: {term}")
                            else:
                                logger.error(
                                    f"方法3输入验证失败: 期望'{term}', 实际'{input_value}'"
                                )
                                raise Exception("JavaScript方法输入验证失败")

                        except Exception as e3:
                            logger.error(f"所有输入方法都失败: {e1}, {e2}, {e3}")
                            await self.element_detector.take_diagnostic_screenshot(
                                page, f"input_all_methods_failed_{term[:20]}.png"
                            )
                            return False

            except Exception as e:
                logger.error(f"输入搜索词过程异常: {e}")
                return False

            logger.debug("准备提交搜索...")

            try:
                logger.debug("尝试方法1: 按 Enter 键")
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)

                current_url = page.url
                if "search" in current_url.lower() or "/search?" in current_url:
                    logger.info("✓ 方法1成功：Enter 键提交搜索")
                else:
                    logger.debug(f"方法1失败，URL未变化: {current_url}")

                    logger.debug("尝试方法2: Escape + Enter")
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.3)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)

                    current_url = page.url
                    if "search" in current_url.lower() or "/search?" in current_url:
                        logger.info("✓ 方法2成功：Escape + Enter 提交搜索")
                    else:
                        logger.debug(f"方法2失败，URL未变化: {current_url}")

                        logger.debug("尝试方法3: 点击搜索按钮")
                        search_button_selectors = [
                            "input#sb_form_go",
                            "button#sb_form_go",
                            "label#search_icon",
                            "button[aria-label*='搜索']",
                            "button[aria-label*='Search']",
                            "input[type='submit']",
                            "button[type='submit']",
                        ]

                        button_clicked = False
                        for selector in search_button_selectors:
                            try:
                                button = await page.query_selector(selector)
                                if button and await button.is_visible():
                                    await button.click()
                                    await asyncio.sleep(2)
                                    button_clicked = True
                                    logger.debug(f"点击了搜索按钮: {selector}")
                                    break
                            except Exception:
                                continue

                        if button_clicked:
                            current_url = page.url
                            if "search" in current_url.lower() or "/search?" in current_url:
                                logger.info("✓ 方法3成功：点击按钮提交搜索")
                            else:
                                logger.warning(f"方法3失败，URL未变化: {current_url}")
                        else:
                            logger.warning("未找到搜索按钮")

                            logger.debug("尝试方法4: JavaScript 提交表单")
                            try:
                                await page.evaluate("""
                                    () => {
                                        const form = document.querySelector('form#sb_form') ||
                                                   document.querySelector('form[action*="search"]') ||
                                                   document.querySelector('form');
                                        if (form) {
                                            form.submit();
                                            return true;
                                        }
                                        return false;
                                    }
                                """)
                                await asyncio.sleep(2)

                                current_url = page.url
                                if "search" in current_url.lower() or "/search?" in current_url:
                                    logger.info("✓ 方法4成功：JavaScript 提交表单")
                                else:
                                    logger.error(f"所有提交方法都失败，当前URL: {current_url}")
                                    await self.element_detector.take_diagnostic_screenshot(
                                        page, f"submit_all_methods_failed_{term[:20]}.png"
                                    )
                            except Exception as e4:
                                logger.error(f"方法4失败: {e4}")

            except Exception as e:
                logger.error(f"提交搜索过程异常: {e}")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"submit_exception_{term[:20]}.png"
                )

            try:
                await self.element_detector.wait_for_page_ready(
                    page, timeout=15000, check_network=True
                )
            except Exception:
                logger.warning("等待页面加载超时，继续...")

            await asyncio.sleep(random.uniform(1, 2))

            current_url = page.url
            if "search" not in current_url.lower() and "/search?" not in current_url:
                logger.warning(f"搜索可能未成功，当前URL: {current_url}")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"search_not_submitted_{term[:20]}.png"
                )
                return False
            else:
                logger.info(f"✓ 搜索已成功提交，当前URL: {current_url}")

            await self.anti_ban.simulate_human_scroll(page)

            if random.random() < 0.3:
                await self._click_random_result(page)

            if random.random() < 0.2:
                await self._random_pagination(page)

            logger.info(f"✓ 搜索完成: {term}")
            return True

        except Exception as e:
            logger.error(f"搜索失败 '{term}': {e}")
            return False

    async def _click_random_result(self, page: Page) -> None:
        """随机点击一个搜索结果（增加真实性）"""
        try:
            logger.debug("尝试点击搜索结果...")

            tab_manager = TabManager(page.context)

            result_links = await self.element_detector.find_search_results(
                page, timeout=5000, min_results=1
            )

            if not result_links:
                logger.debug("未找到搜索结果链接")
                return

            available_links = result_links[: min(5, len(result_links))]
            link = random.choice(available_links)

            try:
                link_text = await link.text_content()
                logger.debug(f"点击搜索结果: {link_text[:50]}...")
            except Exception:
                pass

            original_url = page.url

            success = await tab_manager.click_link_in_current_tab(page, link, timeout=10000)

            if success:
                stay_time = random.uniform(2, 4)
                await asyncio.sleep(stay_time)

                await self.anti_ban.simulate_human_scroll(page)

                try:
                    await page.go_back(wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(random.uniform(1, 2))
                    logger.debug("✓ 搜索结果点击完成")
                except Exception as e:
                    logger.debug(f"后退失败，直接导航回搜索页: {e}")
                    try:
                        await page.goto(original_url, wait_until="domcontentloaded", timeout=10000)
                        await asyncio.sleep(1)
                    except Exception:
                        pass
            else:
                logger.debug("链接点击失败，跳过此次点击")

        except Exception as e:
            logger.debug(f"点击搜索结果失败: {e}")
            try:
                if "bing.com/search" not in page.url:
                    await page.goto(self.BING_URL, wait_until="domcontentloaded", timeout=10000)
            except Exception:
                pass

    async def _random_pagination(self, page: Page) -> None:
        """随机翻页（增加真实性）"""
        try:
            logger.debug("尝试翻页...")

            next_page_selectors = [
                "a[title='Next page']",
                "a.sb_pagN",
                "a:has-text('Next')",
            ]

            next_button = None
            for selector in next_page_selectors:
                try:
                    next_button = await page.query_selector(selector)
                    if next_button:
                        break
                except Exception:
                    continue

            if not next_button:
                logger.debug("未找到翻页按钮")
                return

            await next_button.click()

            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            await asyncio.sleep(random.uniform(1, 2))

            await self.anti_ban.simulate_human_scroll(page)

            await page.go_back()
            await asyncio.sleep(random.uniform(1, 2))

            logger.debug("✓ 翻页完成")

        except Exception as e:
            logger.debug(f"翻页失败: {e}")

    async def execute_desktop_searches(self, page: Page, count: int, health_monitor=None) -> int:
        """执行桌面端搜索"""
        logger.info(f"开始执行 {count} 次桌面搜索...")

        success_count = 0

        for i in range(count):
            term = await self._get_search_term()

            logger.info(f"[{i + 1}/{count}] 搜索: {term}")

            try:
                from src.ui.real_time_status import StatusManager

                StatusManager.update_desktop_searches(i, count)
            except Exception:
                pass

            start_time = time.time() if health_monitor else 0
            search_success = await self.perform_single_search(page, term, health_monitor)

            if search_success:
                success_count += 1
                if health_monitor:
                    response_time = time.time() - start_time
                    health_monitor.record_search_result(True, response_time)
            else:
                logger.warning(f"搜索 {i + 1} 失败，继续...")
                if health_monitor:
                    health_monitor.record_search_result(False)

            if i < count - 1:
                wait_time = self.anti_ban.get_random_wait_time()
                logger.debug(f"等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)

        try:
            from src.ui.real_time_status import StatusManager

            StatusManager.update_desktop_searches(success_count, count)
        except Exception:
            pass

        logger.info(f"✓ 桌面搜索完成: {success_count}/{count} 成功")
        return success_count

    async def execute_mobile_searches(self, page: Page, count: int, health_monitor=None) -> int:
        """执行移动端搜索"""
        logger.info(f"开始执行 {count} 次移动搜索...")

        success_count = 0

        for i in range(count):
            term = await self._get_search_term()

            logger.info(f"[{i + 1}/{count}] 搜索: {term}")

            try:
                from src.ui.real_time_status import StatusManager

                StatusManager.update_mobile_searches(i, count)
            except Exception:
                pass

            start_time = time.time() if health_monitor else 0
            search_success = await self.perform_single_search(page, term, health_monitor)

            if search_success:
                success_count += 1
                if health_monitor:
                    response_time = time.time() - start_time
                    health_monitor.record_search_result(True, response_time)
            else:
                logger.warning(f"搜索 {i + 1} 失败，继续...")
                if health_monitor:
                    health_monitor.record_search_result(False)

            if i < count - 1:
                wait_time = self.anti_ban.get_random_wait_time()
                logger.debug(f"等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)

        try:
            from src.ui.real_time_status import StatusManager

            StatusManager.update_mobile_searches(success_count, count)
        except Exception:
            pass

        logger.info(f"✓ 移动搜索完成: {success_count}/{count} 成功")
        return success_count
