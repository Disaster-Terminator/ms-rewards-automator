"""
搜索引擎模块
执行搜索任务，协调各个组件
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Protocol

from playwright.async_api import Page

from browser.element_detector import ElementDetector
from login.human_behavior_simulator import HumanBehaviorSimulator
from ui.bing_theme_manager import BingThemeManager
from ui.cookie_handler import CookieHandler
from ui.tab_manager import TabManager

logger = logging.getLogger(__name__)


class StatusManagerProtocol(Protocol):
    @classmethod
    def update_desktop_searches(
        cls, current: int, total: int, search_time: float = None
    ) -> None: ...

    @classmethod
    def update_mobile_searches(
        cls, current: int, total: int, search_time: float = None
    ) -> None: ...

    @classmethod
    def update_operation(cls, operation: str) -> None: ...


class SearchEngine:
    """搜索引擎类"""

    BING_URL = "https://www.bing.com"

    def __init__(
        self,
        config,
        term_generator,
        anti_ban,
        monitor=None,
        query_engine=None,
        status_manager: type[StatusManagerProtocol] | None = None,
        human_behavior: HumanBehaviorSimulator | None = None,
    ):
        """
        初始化搜索引擎

        Args:
            config: ConfigManager 实例
            term_generator: SearchTermGenerator 实例
            anti_ban: AntiBanModule 实例
            monitor: StateMonitor 实例（可选）
            query_engine: QueryEngine 实例（可选，用于智能查询生成）
            status_manager: StatusManager 类（可选，用于进度显示，使用 classmethod）
            human_behavior: HumanBehaviorSimulator 实例（可选，用于拟人化行为）
        """
        self.config = config
        self.term_generator = term_generator
        self.anti_ban = anti_ban
        self.monitor = monitor
        self.query_engine = query_engine
        self.status_manager = status_manager
        self.human_behavior = human_behavior or HumanBehaviorSimulator(logger)

        self.element_detector = ElementDetector(config)
        self.theme_manager = BingThemeManager(config)
        self._query_cache = []

        self.human_behavior_level = config.get("anti_detection.human_behavior_level", "medium")
        self.micro_movement_probability = config.get(
            "anti_detection.mouse_movement.micro_movement_probability", 0.3
        )

        logger.info(f"搜索引擎初始化完成，拟人化等级: {self.human_behavior_level}")

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
                        self.config.get("search.desktop_count", 20),
                        self.config.get("search.mobile_count", 0),
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

    def _get_term_source(self, term: str) -> str:
        """获取搜索词来源"""
        if self.query_engine and self.config.get("query_engine.enabled", False):
            return self.query_engine.get_query_source(term)
        return "local_file"

    async def _human_input_search_term(self, page: Page, search_box, term: str) -> bool:
        """
        使用拟人化行为输入搜索词

        Args:
            page: Playwright Page 对象
            search_box: 搜索框元素
            term: 搜索词

        Returns:
            是否成功输入
        """
        try:
            if self.human_behavior_level == "heavy":
                return await self._human_input_heavy(page, search_box, term)
            elif self.human_behavior_level == "medium":
                return await self._human_input_medium(page, search_box, term)
            else:
                return await self._human_input_light(page, search_box, term)
        except Exception as e:
            logger.error(f"拟人化输入失败: {e}")
            return await self._fallback_input(page, search_box, term)

    async def _human_input_heavy(self, page: Page, search_box, term: str) -> bool:
        """完整拟人化输入：贝塞尔曲线移动 + 自然点击 + 正态分布打字"""
        logger.debug("使用 heavy 级别拟人化输入")

        box = await search_box.bounding_box()
        if box:
            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2
            await self.human_behavior.move_mouse_naturally(page, target_x, target_y)
            await self.human_behavior.human_delay(100, 300)

        await search_box.click()
        await self.human_behavior.human_delay(50, 150)

        await page.keyboard.press("Control+A")
        await self.human_behavior.human_delay(50, 100)
        await page.keyboard.press("Backspace")
        await self.human_behavior.human_delay(100, 200)

        for _i, char in enumerate(term):
            await page.keyboard.type(char)
            delay = self.human_behavior.get_typing_delay()
            await asyncio.sleep(delay / 1000.0)
            if random.random() < 0.1:
                await self.human_behavior.human_delay(100, 300)

        if random.random() < self.micro_movement_probability:
            await self.human_behavior.random_mouse_movement(page)

        return await self._verify_input(search_box, term)

    async def _human_input_medium(self, page: Page, search_box, term: str) -> bool:
        """中等拟人化输入：自然点击 + 正态分布打字 + 30%鼠标微动"""
        logger.debug("使用 medium 级别拟人化输入")

        await search_box.click()
        await self.human_behavior.human_delay(100, 200)

        await page.keyboard.press("Control+A")
        await self.human_behavior.human_delay(50, 100)
        await page.keyboard.press("Backspace")
        await self.human_behavior.human_delay(100, 200)

        for _i, char in enumerate(term):
            await page.keyboard.type(char)
            delay = self.human_behavior.get_typing_delay()
            await asyncio.sleep(delay / 1000.0)

        if random.random() < self.micro_movement_probability:
            await self.human_behavior.random_mouse_movement(page)

        return await self._verify_input(search_box, term)

    async def _human_input_light(self, page: Page, search_box, term: str) -> bool:
        """轻量拟人化输入：仅正态分布延迟"""
        logger.debug("使用 light 级别拟人化输入")

        await search_box.click()
        await asyncio.sleep(0.2)

        await page.keyboard.press("Control+A")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)

        for char in term:
            await page.keyboard.type(char)
            delay = self.human_behavior.get_typing_delay()
            await asyncio.sleep(delay / 1000.0)

        return await self._verify_input(search_box, term)

    async def _fallback_input(self, page: Page, search_box, term: str) -> bool:
        """回退输入方法（原有逻辑）"""
        logger.debug("使用回退输入方法")

        try:
            await search_box.fill(term)
            await asyncio.sleep(0.3)
            return await self._verify_input(search_box, term)
        except Exception:
            try:
                await search_box.click()
                await page.keyboard.type(term, delay=50)
                return await self._verify_input(search_box, term)
            except Exception:
                try:
                    await search_box.evaluate(
                        "(el, value) => { el.value = value; }",
                        term,
                    )
                    await search_box.evaluate("""
                        el => {
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    """)
                    return await self._verify_input(search_box, term)
                except Exception:
                    return False

    async def _verify_input(self, search_box, expected: str) -> bool:
        """验证输入是否成功"""
        try:
            input_value = await search_box.input_value()
            if input_value == expected:
                logger.info(f"✓ 成功输入搜索词: {expected}")
                return True
            else:
                logger.warning(f"输入验证失败: 期望'{expected}', 实际'{input_value}'")
                return False
        except Exception as e:
            logger.error(f"验证输入时出错: {e}")
            return False

    async def _human_submit_search(self, page: Page) -> bool:
        """
        使用拟人化行为提交搜索

        Returns:
            是否成功提交
        """
        if self.human_behavior_level in ("medium", "heavy"):
            await self.human_behavior.human_delay(100, 300)

        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        current_url = page.url
        if "search" in current_url.lower() or "/search?" in current_url:
            logger.info("✓ 搜索提交成功")
            return True

        await page.keyboard.press("Escape")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        current_url = page.url
        if "search" in current_url.lower() or "/search?" in current_url:
            logger.info("✓ 搜索提交成功（Escape+Enter）")
            return True

        search_button_selectors = [
            "input#sb_form_go",
            "button#sb_form_go",
            "label#search_icon",
            "button[aria-label*='搜索']",
            "button[aria-label*='Search']",
        ]

        for selector in search_button_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    if self.human_behavior_level == "heavy":
                        await self.human_behavior.human_click(page, selector)
                    else:
                        await button.click()
                    await asyncio.sleep(2)

                    current_url = page.url
                    if "search" in current_url.lower() or "/search?" in current_url:
                        logger.info(f"✓ 搜索提交成功（点击按钮: {selector}）")
                        return True
            except Exception:
                continue

        try:
            await page.evaluate("""
                () => {
                    const form = document.querySelector('form#sb_form') ||
                               document.querySelector('form[action*="search"]') ||
                               document.querySelector('form');
                    if (form) form.submit();
                }
            """)
            await asyncio.sleep(2)

            current_url = page.url
            if "search" in current_url.lower() or "/search?" in current_url:
                logger.info("✓ 搜索提交成功（JavaScript）")
                return True
        except Exception:
            pass

        logger.error("所有提交方法都失败")
        return False

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

            logger.debug("使用拟人化输入...")
            input_success = await self._human_input_search_term(page, search_box, term)

            if not input_success:
                logger.error("拟人化输入失败，尝试回退方法...")
                input_success = await self._fallback_input(page, search_box, term)

            if not input_success:
                logger.error("所有输入方法都失败")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"input_all_methods_failed_{term[:20]}.png"
                )
                return False

            logger.debug("准备提交搜索...")
            submit_success = await self._human_submit_search(page)

            if not submit_success:
                logger.error("搜索提交失败")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"submit_failed_{term[:20]}.png"
                )
                return False

            try:
                await self.element_detector.wait_for_page_ready(
                    page, timeout=15000, check_network=True
                )
            except Exception:
                logger.warning("等待页面加载超时，继续...")

            await asyncio.sleep(random.uniform(1, 2))

            if not await self._verify_search_result(page, term):
                logger.warning(f"搜索结果验证失败: {term}")
                await self.element_detector.take_diagnostic_screenshot(
                    page, f"search_verification_failed_{term[:20]}.png"
                )
                return False

            logger.info("✓ 搜索已成功提交并验证")
            current_url = page.url
            logger.debug(f"当前URL: {current_url}")

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

    async def _verify_search_result(self, page: Page, term: str) -> bool:
        """
        验证搜索结果是否成功

        Args:
            page: Playwright Page 对象
            term: 搜索词

        Returns:
            是否验证成功
        """
        try:
            current_url = page.url
            if "search" not in current_url.lower() and "/search?" not in current_url:
                logger.warning(f"URL 不包含搜索标识: {current_url}")
                return False

            try:
                page_title = await page.title()
                if term.lower() in page_title.lower():
                    logger.debug(f"搜索词出现在页面标题中: {page_title}")
                else:
                    logger.debug(f"搜索词未出现在标题中，但URL有效: {page_title}")
            except Exception:
                pass

            try:
                result_count = await page.evaluate("""
                    () => {
                        const results = document.querySelectorAll('#b_results .b_algo');
                        return results.length;
                    }
                """)

                if result_count and result_count > 0:
                    logger.debug(f"找到 {result_count} 个搜索结果")
                    return True
                else:
                    logger.warning("未找到搜索结果元素")
                    no_result_indicator = await page.query_selector(".b_noresults")
                    if no_result_indicator:
                        logger.info("搜索无结果（但搜索本身成功）")
                        return True
                    logger.warning("未找到搜索结果且无'无结果'指示器，可能遇到错误页面")
                    return False
            except Exception as e:
                logger.debug(f"检查搜索结果数量失败: {e}")
                return False

        except Exception as e:
            logger.error(f"验证搜索结果时出错: {e}")
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
            source = self._get_term_source(term)

            logger.info(f"[{i + 1}/{count}] 搜索: {term} (来源: {source})")

            # 更新进度：当前正在执行第 i+1 次搜索
            if self.status_manager:
                logger.debug(f"更新进度: 桌面搜索 {i}/{count}")
                self.status_manager.update_desktop_searches(i, count)

            search_start = time.time()
            start_time = search_start if health_monitor else 0
            search_success = await self.perform_single_search(page, term, health_monitor)
            search_time = time.time() - search_start

            if search_success:
                success_count += 1
                if health_monitor:
                    response_time = time.time() - start_time
                    health_monitor.record_search_result(True, response_time)
                # 更新搜索计数
                if self.monitor:
                    self.monitor.session_data["desktop_searches"] += 1
            else:
                logger.warning(f"搜索 {i + 1} 失败，继续...")
                if health_monitor:
                    health_monitor.record_search_result(False)

            # 更新进度：第 i+1 次搜索完成
            if self.status_manager:
                logger.debug(f"更新进度: 桌面搜索完成 {i + 1}/{count}")
                self.status_manager.update_desktop_searches(i + 1, count, search_time)

            if i < count - 1:
                wait_time = self.anti_ban.get_random_wait_time()
                logger.debug(f"等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)

        logger.info(f"✓ 桌面搜索完成: {success_count}/{count} 成功")
        return success_count

    async def execute_mobile_searches(self, page: Page, count: int, health_monitor=None) -> int:
        """执行移动端搜索"""
        logger.info(f"开始执行 {count} 次移动搜索...")

        success_count = 0

        for i in range(count):
            term = await self._get_search_term()
            source = self._get_term_source(term)

            logger.info(f"[{i + 1}/{count}] 搜索: {term} (来源: {source})")

            # 更新进度：当前正在执行第 i+1 次搜索
            if self.status_manager:
                logger.debug(f"更新进度: 移动搜索 {i}/{count}")
                self.status_manager.update_mobile_searches(i, count)

            search_start = time.time()
            start_time = search_start if health_monitor else 0
            search_success = await self.perform_single_search(page, term, health_monitor)
            search_time = time.time() - search_start

            if search_success:
                success_count += 1
                if health_monitor:
                    response_time = time.time() - start_time
                    health_monitor.record_search_result(True, response_time)
                # 更新搜索计数
                if self.monitor:
                    self.monitor.session_data["mobile_searches"] += 1
            else:
                logger.warning(f"搜索 {i + 1} 失败，继续...")
                if health_monitor:
                    health_monitor.record_search_result(False)

            # 更新进度：第 i+1 次搜索完成
            if self.status_manager:
                logger.debug(f"更新进度: 移动搜索完成 {i + 1}/{count}")
                self.status_manager.update_mobile_searches(i + 1, count, search_time)

            if i < count - 1:
                wait_time = self.anti_ban.get_random_wait_time()
                logger.debug(f"等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)

        logger.info(f"✓ 移动搜索完成: {success_count}/{count} 成功")
        return success_count

    async def close(self):
        """关闭搜索引擎，释放资源"""
        if self.query_engine:
            try:
                await self.query_engine.close()
                logger.debug("QueryEngine 已关闭")
            except Exception as e:
                logger.debug(f"关闭 QueryEngine 失败: {e}")
