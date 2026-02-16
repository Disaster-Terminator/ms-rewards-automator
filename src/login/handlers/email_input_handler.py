"""
Email Input Handler.

Handles the email input state in Microsoft login flow.
"""

from typing import Any

from ..edge_popup_handler import EdgePopupHandler
from ..login_state_machine import LoginState
from ..state_handler import StateHandler


class EmailInputHandler(StateHandler):
    """
    Handler for email input state.

    This handler:
    1. Detects the email input page
    2. Fills in the email address
    3. Clicks the "Next" button
    """

    def __init__(self, *args, **kwargs):
        """Initialize handler with Edge popup handler."""
        super().__init__(*args, **kwargs)
        self.edge_popup_handler = EdgePopupHandler(logger=self.logger)

    # Common selectors for email input
    EMAIL_INPUT_SELECTORS = [
        'input[type="email"]',
        'input[name="loginfmt"]',
        'input[id="i0116"]',
    ]

    NEXT_BUTTON_SELECTORS = [
        # 新版页面选择器（优先）
        'button[type="submit"]',
        'input[type="submit"][id="idSIButton9"]',
        # 通用选择器
        'input[type="submit"]',
        'input[id="idSIButton9"]',
        'button[id="idSIButton9"]',
        # 文本匹配（最后备选）
        'button:has-text("Next")',
        'button:has-text("下一步")',
    ]

    async def can_handle(self, page: Any) -> bool:
        """
        Check if current page is the email input page.

        Args:
            page: Playwright page object

        Returns:
            True if email input page detected
        """
        # 快速检查：先检查 URL 是否包含登录相关关键词
        url = page.url.lower()
        if "login" not in url and "microsoft" not in url:
            return False

        # Check for email input field (reduced timeout for speed)
        for selector in self.EMAIL_INPUT_SELECTORS:
            if await self.element_exists(page, selector, timeout=1000):
                self.logger.debug(f"Email input detected: {selector}")
                return True

        return False

    async def handle(self, page: Any, credentials: dict[str, str]) -> bool:
        """
        Handle email input by filling email and clicking next.

        Args:
            page: Playwright page object
            credentials: Must contain 'email' key

        Returns:
            True if successful
        """
        email = credentials.get("email")
        if not email:
            self.logger.error("No email provided in credentials")
            return False

        self.logger.info(f"Handling email input for: {email}")

        # 首先尝试关闭可能的 Edge 弹窗
        await self.edge_popup_handler.dismiss_popup(page)

        # Small delay before interaction (simulate reading the page)
        await self.human_simulator.human_delay(800, 1500)

        # Find and fill email input with human-like typing
        filled = False
        for selector in self.EMAIL_INPUT_SELECTORS:
            if await self.safe_fill(page, selector, email, timeout=5000, human_like=True):
                filled = True
                self.logger.debug(f"Email filled using selector: {selector}")
                break

        if not filled:
            self.logger.error("Failed to fill email input")
            return False

        # Delay after typing (simulate checking what was typed)
        await self.human_simulator.human_delay(500, 1200)

        # Click next button with human-like behavior
        clicked = False
        for selector in self.NEXT_BUTTON_SELECTORS:
            if await self.safe_click(page, selector, timeout=5000, human_like=True):
                clicked = True
                self.logger.debug(f"Next button clicked using selector: {selector}")
                break

        if not clicked:
            self.logger.error("Failed to click next button")
            return False

        # Wait for navigation
        await self.wait_for_navigation(page)

        self.logger.info("Email input handled successfully")
        return True

    def get_next_states(self) -> list[LoginState]:
        """
        Possible next states after email input.

        Returns:
            List of possible next states
        """
        return [
            LoginState.PASSWORD_INPUT,
            LoginState.PASSWORDLESS,
            LoginState.GET_A_CODE,
            LoginState.ERROR,
        ]
