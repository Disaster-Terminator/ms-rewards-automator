"""
Passwordless Handler.

Handles Microsoft's passwordless authentication flow.
"""

from typing import Any

from ..edge_popup_handler import EdgePopupHandler
from ..login_state_machine import LoginState
from ..state_handler import StateHandler


class PasswordlessHandler(StateHandler):
    """
    Handler for passwordless authentication state.

    This handler detects passwordless prompts and clicks
    the appropriate option to use password instead.
    """

    def __init__(self, *args, **kwargs):
        """Initialize handler with Edge popup handler."""
        super().__init__(*args, **kwargs)
        self.edge_popup_handler = EdgePopupHandler(logger=self.logger)

    # Selectors for passwordless page
    PASSWORDLESS_INDICATORS = [
        "text=Use your password instead",
        "text=Sign in another way",
        "text=Other ways to sign in",
        "text=Use your password",  # 新增
    ]

    USE_PASSWORD_SELECTORS = [
        # ✅ 已验证成功的选择器（最优先）
        'div:has(svg) >> text="Use your password"',
        # 精确匹配选择器
        'div[data-value="Password"]',
        'div:text-is("Use your password")',
        '[data-value="Password"]',
        # 通用选择器
        'div:has-text("Use your password")',
        '[role="button"]:has-text("Use your password")',
        'button:has-text("Use your password")',
        'a:has-text("Use your password")',
        # 中文版本
        'div:has(svg) >> text="使用密码"',
        'div:text-is("使用密码")',
        'div:has-text("使用密码")',
        # 旧版选择器（向后兼容）
        'a:has-text("Use your password instead")',
        'button:has-text("Use your password instead")',
        'a:has-text("以其他方式登录")',
        'a:has-text("Sign in another way")',
        'a[id="signInAnotherWay"]',
        'a[id="idA_PWD_SwitchToPassword"]',
        'button[id="idA_PWD_SwitchToPassword"]',
    ]

    async def can_handle(self, page: Any) -> bool:
        """
        Check if current page is passwordless prompt.

        Important: Must NOT match TOTP 2FA pages which may also have
        "Sign in another way" text.

        Args:
            page: Playwright page object

        Returns:
            True if passwordless page detected (and NOT TOTP page)
        """
        # 快速检查：先检查 URL
        url = page.url.lower()
        if "login" not in url and "microsoft" not in url:
            return False

        # First, exclude TOTP pages (they have priority)
        totp_indicators = [
            'input[name="otc"]',
            'input[id="idTxtBx_SAOTCC_OTC"]',
            "text=Enter the code from your authenticator app",
            "text=Enter code",
        ]

        for indicator in totp_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.debug(f"TOTP indicator found, not passwordless: {indicator}")
                    return False
            except Exception:
                pass

        # Now check for passwordless indicators
        for indicator in self.PASSWORDLESS_INDICATORS:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.debug(f"Passwordless indicator found: {indicator}")
                    return True
            except Exception:
                pass

        return False

    async def handle(self, page: Any, credentials: dict[str, str]) -> bool:
        """
        Handle passwordless by clicking "Use password instead".

        Args:
            page: Playwright page object
            credentials: Not used for this handler

        Returns:
            True if successful
        """
        self.logger.info("Handling passwordless authentication")

        # 首先尝试关闭可能的 Edge 弹窗（使用专用处理器）
        await self.edge_popup_handler.dismiss_popup(page, wait_after=2000)

        # 策略1: 尝试标准选择器点击
        clicked = False
        for selector in self.USE_PASSWORD_SELECTORS:
            try:
                element = await page.wait_for_selector(selector, timeout=3000, state="visible")
                if element:
                    await element.click()
                    self.logger.info(f"✓ 成功点击: {selector}")
                    clicked = True
                    break
            except Exception as e:
                self.logger.debug(f"选择器失败 {selector}: {e}")
                continue

        # 如果点击成功，保存 HTML 用于验证
        if clicked:
            try:
                import os
                from datetime import datetime

                os.makedirs("logs/diagnostics", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_path = f"logs/diagnostics/passwordless_clicked_{timestamp}.html"
                content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"点击后 HTML 已保存: {html_path}")
            except Exception as e:
                self.logger.debug(f"保存 HTML 失败: {e}")

        # 策略2: 如果标准点击失败，尝试 JavaScript 点击
        if not clicked:
            self.logger.warning("标准选择器失败，尝试 JavaScript 点击...")
            js_selectors = [
                'div[data-value="Password"]',
                'div:has-text("Use your password")',
            ]
            for selector in js_selectors:
                try:
                    result = await page.evaluate(f"""
                        () => {{
                            const element = document.querySelector('{selector}');
                            if (element) {{
                                element.click();
                                return true;
                            }}
                            return false;
                        }}
                    """)
                    if result:
                        self.logger.info(f"✓ JavaScript 点击成功: {selector}")
                        clicked = True
                        break
                except Exception as e:
                    self.logger.debug(f"JS 点击失败 {selector}: {e}")
                    continue

        if not clicked:
            self.logger.error("所有点击策略均失败")
            self.logger.info("保存截图和 HTML 用于调试...")
            try:
                import os
                from datetime import datetime

                os.makedirs("logs/diagnostics", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # 保存截图
                screenshot_path = f"logs/diagnostics/passwordless_{timestamp}.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"截图已保存: {screenshot_path}")

                # 保存 HTML
                html_path = f"logs/diagnostics/passwordless_{timestamp}.html"
                content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"HTML 已保存: {html_path}")
            except Exception as e:
                self.logger.error(f"保存调试信息失败: {e}")
            return False

        # Wait for navigation
        await self.wait_for_navigation(page)

        self.logger.info("Passwordless handled successfully")
        return True

    def get_next_states(self) -> list[LoginState]:
        """
        Possible next states after passwordless.

        Returns:
            List of possible next states
        """
        return [
            LoginState.PASSWORD_INPUT,
            LoginState.ERROR,
        ]
