"""
Auth Blocked Handler.

Handles Microsoft's "Please retry with a different device" error page.
This occurs when Microsoft's anti-automation system blocks the login attempt.
"""

import asyncio
from typing import Any

from ..login_state_machine import LoginState
from ..state_handler import StateHandler


class AuthBlockedHandler(StateHandler):
    """
    Handler for authentication blocked state.

    This handler detects when Microsoft blocks the login attempt
    and implements retry logic with exponential backoff.
    """

    # Selectors that indicate auth blocked page
    AUTH_BLOCKED_INDICATORS = [
        "text=Please retry with a different device",
        "text=retry with a different device",
        "text=other authentication method",
        "text=请使用其他设备重试",
        "text=使用其他身份验证方法",
    ]

    def __init__(self, *args, **kwargs):
        """Initialize handler with retry tracking."""
        super().__init__(*args, **kwargs)
        self.retry_count = 0
        self.max_retries = 3
        self.base_delay = 10  # seconds

    async def can_handle(self, page: Any) -> bool:
        """
        Check if current page is the auth blocked page.

        Args:
            page: Playwright page object

        Returns:
            True if auth blocked page detected
        """
        for indicator in self.AUTH_BLOCKED_INDICATORS:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.warning(f"Auth blocked detected: {indicator}")
                    return True
            except Exception:
                pass

        return False

    async def handle(self, page: Any, credentials: dict[str, str]) -> bool:
        """
        Handle auth blocked by implementing retry logic.

        Strategy:
        1. Increment retry counter
        2. If max retries exceeded, return False (give up)
        3. Wait with exponential backoff
        4. Navigate back to login page to restart

        Args:
            page: Playwright page object
            credentials: Not used for this handler

        Returns:
            True if retry initiated, False if max retries exceeded
        """
        self.retry_count += 1

        if self.retry_count > self.max_retries:
            self.logger.error(f"Auth blocked: Max retries ({self.max_retries}) exceeded")
            return False

        # Calculate delay with exponential backoff
        delay = self.base_delay * (2 ** (self.retry_count - 1))

        self.logger.warning(
            f"Auth blocked (attempt {self.retry_count}/{self.max_retries}). "
            f"Waiting {delay}s before retry..."
        )

        # Wait before retry
        await asyncio.sleep(delay)

        # Navigate back to login page to restart
        try:
            await page.goto("https://login.live.com", wait_until="domcontentloaded")
            self.logger.info("Navigated back to login page for retry")
        except Exception as e:
            self.logger.error(f"Failed to navigate to login page: {e}")
            return False

        return True

    def get_next_states(self) -> list[LoginState]:
        """
        Possible next states after auth blocked.

        Returns:
            List of possible next states
        """
        return [
            LoginState.EMAIL_INPUT,  # Restart login flow
            LoginState.ERROR,
        ]
