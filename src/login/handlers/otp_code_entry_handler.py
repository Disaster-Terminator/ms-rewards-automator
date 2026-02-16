"""
OTP Code Entry Handler.

Handles pages where Microsoft asks for email/SMS verification code.
Attempts to bypass and return to password login.
"""

from typing import Any

from ..login_state_machine import LoginState
from ..state_handler import StateHandler


class OtpCodeEntryHandler(StateHandler):
    """
    Handler for OTP code entry state.

    This handler attempts to bypass the OTP requirement and
    return to password-based login.

    Strategy (from TS project):
    1. Try clicking "Use your password" in footer
    2. Try clicking back button
    3. If all fail, return False to trigger retry
    """

    # Selectors for OTP code entry page
    OTP_PAGE_INDICATORS = [
        '[data-testid="codeEntry"]',
        'input[name="otc"][type="tel"]',  # Different from TOTP
        "text=Enter the code we sent to",
        "text=Enter the access code",
        "text=输入我们发送的代码",
    ]

    # Selectors to bypass OTP
    BYPASS_SELECTORS = [
        '[data-testid="viewFooter"] >> [role="button"]',  # "Use your password"
        "text=Use your password",
        "text=使用密码",
        "#back-button",
        'button[aria-label="Back"]',
    ]

    async def can_handle(self, page: Any) -> bool:
        """
        Check if current page is OTP code entry page.

        Args:
            page: Playwright page object

        Returns:
            True if OTP code entry page detected
        """
        for selector in self.OTP_PAGE_INDICATORS:
            if await self.element_exists(page, selector, timeout=2000):
                self.logger.debug(f"OTP code entry page detected: {selector}")
                return True

        return False

    async def handle(self, page: Any, credentials: dict[str, str]) -> bool:
        """
        Attempt to bypass OTP code entry and return to password login.

        Args:
            page: Playwright page object
            credentials: Not used

        Returns:
            True if bypass attempted (may not succeed)
        """
        self.logger.info("尝试绕过 OTP 验证码页面")

        # 尝试多种绕过方法
        for selector in self.BYPASS_SELECTORS:
            if await self.safe_click(page, selector, timeout=3000, human_like=True):
                self.logger.info(f"成功点击绕过按钮: {selector}")
                await page.wait_for_timeout(2000)
                return True

        self.logger.warning("无法绕过 OTP 验证码页面，所有选择器都失败")
        return False

    def get_next_states(self) -> list[LoginState]:
        """
        Possible next states after OTP bypass attempt.

        Returns:
            List of possible next states
        """
        return [
            LoginState.PASSWORD_INPUT,
            LoginState.PASSWORDLESS,
            LoginState.ERROR,
        ]
