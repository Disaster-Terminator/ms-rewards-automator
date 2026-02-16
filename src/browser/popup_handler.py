"""
Browser Popup Handler - 浏览器弹窗处理器

处理各种浏览器弹窗，包括 Edge 登录促销弹窗、对话框等。
从 login 模块解耦，移到 browser 模块。
"""

import asyncio
import logging
from typing import Any


class BrowserPopupHandler:
    """
    浏览器弹窗处理器

    提供多种策略来检测和处理浏览器弹窗。
    """

    # Comprehensive selector list for Edge popups
    POPUP_SELECTORS = [
        # 中文按钮 - 各种变体
        'button:has-text("不，谢谢")',
        'button:has-text("不, 谢谢")',
        'button:has-text("不谢谢")',
        'button:text-is("不，谢谢")',
        'button:text-is("不, 谢谢")',
        'button:has-text("以后再说")',
        'button:has-text("暂不")',
        'button:has-text("取消")',
        'button:has-text("关闭")',
        # 英文按钮 - 各种变体
        'button:has-text("No, thanks")',
        'button:has-text("No thanks")',
        'button:has-text("No,thanks")',
        'button:text-is("No, thanks")',
        'button:text-is("No thanks")',
        'button:has-text("Not now")',
        'button:has-text("Maybe later")',
        'button:has-text("Skip")',
        'button:has-text("Cancel")',
        'button:has-text("Close")',
        'button:has-text("Dismiss")',
        # 通配符文本匹配
        'button:text-matches(".*[Nn]o.*thank.*", "i")',
        'button:text-matches(".*不.*谢.*", "i")',
        'button:text-matches(".*dismiss.*", "i")',
        # ID 和 Class 选择器
        'button[id*="dismiss"]',
        'button[id*="Dismiss"]',
        'button[id*="cancel"]',
        'button[id*="Cancel"]',
    ]

    def __init__(self, logger: logging.Logger | None = None):
        """初始化弹窗处理器"""
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._popup_handled = False

    async def dismiss_popup(self, page: Any, wait_after: int = 500, debug: bool = False) -> bool:
        """
        尝试关闭弹窗

        Args:
            page: Playwright Page 对象
            wait_after: 关闭后等待时间（毫秒）
            debug: 是否输出调试信息

        Returns:
            True if popup was detected and dismissed, False otherwise
        """
        self._popup_handled = False

        # 检查是否是"保持登录"页面（跳过弹窗处理）
        try:
            title = await page.title()
            if title and ("stay signed in" in title.lower() or "保持登录" in title):
                self.logger.debug(f"检测到'保持登录'页面 (标题: {title})，跳过弹窗处理")
                return False
        except Exception:
            pass

        # 检查页面内容（作为后备）
        try:
            stay_signed_in_element = await page.query_selector('h1:has-text("Stay signed in")')
            if stay_signed_in_element:
                self.logger.debug("检测到'保持登录'页面 (找到标题元素)，跳过弹窗处理")
                return False
        except Exception:
            pass

        # 先检测是否有弹窗
        popup_detected = await self.is_popup_present(page)

        if popup_detected and debug:
            # 保存截图用于调试
            try:
                import os
                from datetime import datetime

                os.makedirs("logs/diagnostics", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"logs/diagnostics/popup_{timestamp}.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"弹窗截图已保存: {screenshot_path}")
            except Exception as e:
                self.logger.debug(f"保存弹窗截图失败: {e}")

        if not popup_detected:
            return False

        self.logger.info("检测到弹窗，尝试关闭...")

        # 策略1: 使用对话框事件自动接受/关闭
        dialog_closed = await self._handle_with_dialog_event(page)
        if dialog_closed:
            self.logger.info("✓ 通过对话框事件关闭弹窗")
            self._popup_handled = True
            await page.wait_for_timeout(wait_after)
            return True

        # 策略2: 尝试点击关闭按钮
        button_clicked = await self._click_dismiss_button(page)
        if button_clicked:
            self.logger.info("✓ 通过点击按钮关闭弹窗")
            self._popup_handled = True
            await page.wait_for_timeout(wait_after)
            return True

        # 策略3: 使用键盘事件
        keyboard_closed = await self._handle_with_keyboard(page)
        if keyboard_closed:
            self.logger.info("✓ 通过键盘事件关闭弹窗")
            self._popup_handled = True
            await page.wait_for_timeout(wait_after)
            return True

        self.logger.warning("⚠ 未能关闭弹窗")
        return False

    async def is_popup_present(self, page: Any, timeout: int = 1000) -> bool:
        """
        检测页面上是否存在弹窗

        Args:
            page: Playwright Page 对象
            timeout: 超时时间（毫秒）

        Returns:
            True if popup is present, False otherwise
        """
        # 策略1: 检查弹窗容器
        popup_container_selectors = [
            '[role="dialog"]',
            '[aria-modal="true"]',
            ".edgepopup",  # 假设的选择器
            "#edge-popup",  # 假设的选择器
        ]

        for selector in popup_container_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible(timeout=timeout):
                    self.logger.debug(f"检测到弹窗容器: {selector}")
                    return True
            except Exception:
                continue

        # 策略2: 检查是否有任何弹窗按钮可见
        for selector in self.POPUP_SELECTORS[:10]:  # 只检查前10个常用选择器
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible(timeout=timeout):
                    self.logger.debug(f"检测到弹窗按钮: {selector}")
                    return True
            except Exception:
                continue

        # 策略3: 检查页面是否有 dialog/modal 角色
        try:
            dialogs = await page.query_selector_all('[role="dialog"], [role="alertdialog"]')
            for dialog in dialogs:
                if await dialog.is_visible(timeout=timeout):
                    self.logger.debug("检测到 dialog 元素")
                    return True
        except Exception:
            pass

        return False

    async def _handle_with_dialog_event(self, page: Any) -> bool:
        """使用对话框事件处理弹窗"""
        dialog_handled = False

        def handle_dialog(dialog):
            nonlocal dialog_handled
            self.logger.debug(f"拦截到对话框: {dialog.type} - {dialog.message}")
            # 尝试接受或关闭对话框
            try:
                # 大多数促销弹窗可以简单地关闭
                asyncio.create_task(dialog.dismiss())
                dialog_handled = True
            except Exception:
                pass

        page.on("dialog", handle_dialog)

        # 等待一小段时间看是否有对话框出现
        await page.wait_for_timeout(500)

        # 移除监听器
        try:
            page.remove_listener("dialog", handle_dialog)
        except Exception:
            pass

        return dialog_handled

    async def _click_dismiss_button(self, page: Any) -> bool:
        """尝试点击关闭按钮"""
        # 尝试各种关闭按钮选择器
        for selector in self.POPUP_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible(timeout=2000):
                    await element.click()
                    self.logger.debug(f"成功点击关闭按钮: {selector}")
                    return True
            except Exception:
                continue

        return False

    async def _handle_with_keyboard(self, page: Any) -> bool:
        """使用键盘事件关闭弹窗"""
        try:
            # 按 Escape 键
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)

            # 如果 Escape 不起作用，尝试按 Tab 然后 Enter
            if not await self.is_popup_present(page, timeout=500):
                return True

            await page.keyboard.press("Tab")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(300)

            return not await self.is_popup_present(page, timeout=500)
        except Exception as e:
            self.logger.debug(f"键盘处理失败: {e}")
            return False


# 兼容性别名
EdgePopupHandler = BrowserPopupHandler
