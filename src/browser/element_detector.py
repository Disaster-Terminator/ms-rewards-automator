"""
元素检测器模块
提供鲁棒的页面元素检测机制，支持多重选择器和降级策略
"""

import asyncio
import logging
from typing import Any

from playwright.async_api import ElementHandle, Page

logger = logging.getLogger(__name__)


class ElementDetector:
    """页面元素检测器类"""

    # 搜索框选择器列表（按优先级排序）
    SEARCH_BOX_SELECTORS = [
        "input[name='q']",  # 标准Bing搜索框
        "input#sb_form_q",  # Bing搜索框ID
        "textarea[name='q']",  # 文本域形式的搜索框
        "input[type='search']",  # 搜索类型输入框
        "input[placeholder*='search']",  # 包含search的占位符
        "input[placeholder*='Search']",  # 包含Search的占位符
        "input[aria-label*='search']",  # 搜索相关的aria标签
        "input[aria-label*='Search']",  # 搜索相关的aria标签
        "input.sb_form_q",  # Bing搜索框类名
        "input[data-testid*='search']",  # 测试ID包含search
        "form input[type='text']",  # 表单中的文本输入框
    ]

    # 搜索按钮选择器
    SEARCH_BUTTON_SELECTORS = [
        "input[type='submit'][value*='Search']",
        "button[type='submit']",
        "input#sb_form_go",
        "button.sb_form_go",
        "button[aria-label*='search']",
        "button[aria-label*='Search']",
    ]

    # 搜索结果选择器
    SEARCH_RESULT_SELECTORS = [
        "li.b_algo h2 a",
        "#b_results .b_algo h2 a",
        "h2 a[href]",
        "li.b_algo a[href]",
        "#b_results li a[href]",
        ".b_algo a[href]",
    ]

    def __init__(self, config=None):
        """
        初始化元素检测器

        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.detection_timeout = 10000  # 默认检测超时时间
        self.retry_count = 3  # 默认重试次数

        # 使用类常量作为实例属性，便于测试
        self.search_box_selectors = self.SEARCH_BOX_SELECTORS.copy()
        self.search_button_selectors = self.SEARCH_BUTTON_SELECTORS.copy()
        self.search_result_selectors = self.SEARCH_RESULT_SELECTORS.copy()

        if config:
            self.detection_timeout = config.get("element_detection.timeout", 10000)
            self.retry_count = config.get("element_detection.retry_count", 3)

        logger.info("元素检测器初始化完成")

    async def find_search_box(
        self, page: Page, timeout: int | None = None, visible_only: bool = True
    ) -> ElementHandle | None:
        """
        查找搜索框元素

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
            visible_only: 是否只查找可见元素

        Returns:
            搜索框元素或None
        """
        timeout = timeout or self.detection_timeout

        logger.debug("开始查找搜索框...")

        for i, selector in enumerate(self.search_box_selectors):
            try:
                logger.debug(f"尝试选择器 {i + 1}/{len(self.search_box_selectors)}: {selector}")

                # 设置状态要求
                state = "visible" if visible_only else "attached"

                element = await page.wait_for_selector(
                    selector,
                    timeout=min(timeout // len(self.search_box_selectors), 2000),
                    state=state,
                )

                if element:
                    # 验证元素是否真的可用
                    if await self._validate_search_box(element):
                        logger.debug(f"✓ 找到搜索框: {selector}")
                        return element
                    else:
                        logger.debug(f"搜索框验证失败: {selector}")
                        continue

            except Exception as e:
                logger.debug(f"选择器失败 {selector}: {e}")
                continue

        logger.warning("未找到可用的搜索框")
        return None

    async def _validate_search_box(self, element: ElementHandle) -> bool:
        """
        验证搜索框元素是否可用

        Args:
            element: 元素句柄

        Returns:
            是否可用
        """
        try:
            # 检查元素是否可见
            is_visible = await element.is_visible()
            if not is_visible:
                return False

            # 检查元素是否可编辑
            is_editable = await element.is_editable()
            if not is_editable:
                return False

            # 检查元素类型
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name not in ["input", "textarea"]:
                return False

            # 检查input类型（如果是input元素）
            if tag_name == "input":
                input_type = await element.get_attribute("type")
                if input_type and input_type.lower() not in ["text", "search", ""]:
                    return False

            return True

        except Exception as e:
            logger.debug(f"搜索框验证出错: {e}")
            return False

    async def find_search_results(
        self, page: Page, timeout: int | None = None, min_results: int = 1
    ) -> list[ElementHandle]:
        """
        查找搜索结果链接

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
            min_results: 最少结果数量

        Returns:
            搜索结果元素列表
        """
        timeout = timeout or self.detection_timeout

        logger.debug("开始查找搜索结果...")

        per_selector_timeout = max(timeout // len(self.search_result_selectors), 2000)

        for i, selector in enumerate(self.search_result_selectors):
            try:
                logger.debug(
                    f"尝试结果选择器 {i + 1}/{len(self.search_result_selectors)}: {selector}"
                )

                await page.wait_for_selector(
                    selector, timeout=per_selector_timeout, state="visible"
                )

                # 获取所有匹配的结果
                elements = await page.query_selector_all(selector)

                if len(elements) >= min_results:
                    # 验证结果链接
                    valid_elements = []
                    for element in elements:
                        if await self._validate_search_result(element):
                            valid_elements.append(element)

                    if len(valid_elements) >= min_results:
                        logger.debug(f"✓ 找到 {len(valid_elements)} 个有效搜索结果: {selector}")
                        return valid_elements

            except Exception as e:
                logger.debug(f"结果选择器失败 {selector}: {e}")
                continue

        logger.warning("未找到足够的搜索结果")
        return []

    async def _validate_search_result(self, element: ElementHandle) -> bool:
        """
        验证搜索结果链接是否有效

        Args:
            element: 元素句柄

        Returns:
            是否有效
        """
        try:
            # 检查是否可见
            is_visible = await element.is_visible()
            if not is_visible:
                return False

            # 检查是否有href属性
            href = await element.get_attribute("href")
            if not href or href in ["#", "javascript:void(0)", "javascript:"]:
                return False

            # 检查链接文本
            text = await element.text_content()
            if not text or len(text.strip()) < 3:
                return False

            return True

        except Exception as e:
            logger.debug(f"搜索结果验证出错: {e}")
            return False

    async def find_element_with_fallback(
        self, page: Page, selectors: list[str], timeout: int | None = None, state: str = "visible"
    ) -> ElementHandle | None:
        """
        使用降级策略查找元素

        Args:
            page: Playwright页面对象
            selectors: 选择器列表（按优先级排序）
            timeout: 超时时间（毫秒）
            state: 元素状态要求

        Returns:
            找到的元素或None
        """
        timeout = timeout or self.detection_timeout

        for i, selector in enumerate(selectors):
            try:
                logger.debug(f"尝试选择器 {i + 1}/{len(selectors)}: {selector}")

                element = await page.wait_for_selector(
                    selector, timeout=min(timeout // len(selectors), 2000), state=state
                )

                if element:
                    logger.debug(f"✓ 找到元素: {selector}")
                    return element

            except Exception as e:
                logger.debug(f"选择器失败 {selector}: {e}")
                continue

        return None

    async def wait_for_page_ready(
        self, page: Page, timeout: int | None = None, check_network: bool = True
    ) -> bool:
        """
        等待页面准备就绪

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
            check_network: 是否检查网络空闲

        Returns:
            页面是否准备就绪
        """
        timeout = timeout or self.detection_timeout

        try:
            logger.debug("等待页面准备就绪...")

            # 等待DOM内容加载
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)

            # 可选：等待网络空闲
            if check_network:
                try:
                    await page.wait_for_load_state("networkidle", timeout=min(timeout, 5000))
                except TimeoutError:
                    logger.debug("网络空闲等待超时，继续...")

            # 等待一小段时间让JavaScript执行
            await asyncio.sleep(0.5)

            logger.debug("✓ 页面准备就绪")
            return True

        except Exception as e:
            logger.warning(f"等待页面准备就绪失败: {e}")
            return False

    async def detect_page_errors(self, page: Page) -> list[str]:
        """
        检测页面错误

        Args:
            page: Playwright页面对象

        Returns:
            错误信息列表
        """
        errors = []

        try:
            # 检查页面标题
            title = await page.title()
            if any(
                error_keyword in title.lower()
                for error_keyword in ["error", "404", "not found", "access denied", "forbidden"]
            ):
                errors.append(f"页面标题包含错误信息: {title}")

            # 检查URL
            url = page.url
            if any(error_keyword in url.lower() for error_keyword in ["error", "404", "notfound"]):
                errors.append(f"URL包含错误信息: {url}")

            # 检查页面内容中的错误信息
            try:
                error_selectors = [
                    "div.error",
                    ".error-message",
                    "[class*='error']",
                    "div:has-text('Error')",
                    "div:has-text('404')",
                ]

                for selector in error_selectors:
                    try:
                        error_elements = await page.query_selector_all(selector)
                        for element in error_elements:
                            if await element.is_visible():
                                text = await element.text_content()
                                if text and len(text.strip()) > 0:
                                    errors.append(f"页面错误元素: {text[:100]}")
                                    break
                    except Exception:
                        continue
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"检测页面错误时出错: {e}")

        return errors

    async def take_diagnostic_screenshot(
        self, page: Page, filename: str, full_page: bool = True
    ) -> bool:
        """
        拍摄诊断截图

        Args:
            page: Playwright页面对象
            filename: 截图文件名
            full_page: 是否全页截图

        Returns:
            是否成功
        """
        try:
            import os

            # 确保screenshots目录存在
            os.makedirs("screenshots", exist_ok=True)

            # 生成完整路径
            filepath = f"screenshots/{filename}"

            # 拍摄截图
            await page.screenshot(path=filepath, full_page=full_page)

            logger.info(f"诊断截图已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"保存诊断截图失败: {e}")
            return False

    async def get_element_info(self, element: ElementHandle) -> dict[str, Any]:
        """
        获取元素详细信息（用于调试）

        Args:
            element: 元素句柄

        Returns:
            元素信息字典
        """
        try:
            info = {}

            # 基本属性
            info["tag_name"] = await element.evaluate("el => el.tagName.toLowerCase()")
            info["is_visible"] = await element.is_visible()
            info["is_enabled"] = await element.is_enabled()

            # 属性
            attributes = await element.evaluate("""
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            info["attributes"] = attributes

            # 文本内容
            info["text_content"] = await element.text_content()
            info["inner_text"] = await element.inner_text()

            # 位置信息
            box = await element.bounding_box()
            info["bounding_box"] = box

            return info

        except Exception as e:
            logger.debug(f"获取元素信息失败: {e}")
            return {"error": str(e)}
