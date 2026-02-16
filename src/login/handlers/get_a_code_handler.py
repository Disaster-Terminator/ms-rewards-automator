"""
Get A Code Handler.

Handles the "Get a code" 2FA method that requires manual intervention.
"""

from typing import Any

from ..login_state_machine import LoginState
from ..state_handler import StateHandler


class GetACodeHandler(StateHandler):
    """
    Handler for "Get a code" 2FA state.

    This handler detects the "Get a code" page and logs
    instructions for manual intervention. It cannot proceed
    automatically as it requires user to check email/SMS.
    """

    # Selectors for "Get a code" page
    GET_A_CODE_INDICATORS = [
        "text=Get a code",
        "text=We need to verify your identity",
        "text=Enter the code we sent to",
    ]

    async def can_handle(self, page: Any) -> bool:
        """
        Check if current page is "Get a code" page.

        Args:
            page: Playwright page object

        Returns:
            True if "Get a code" page detected
        """
        for indicator in self.GET_A_CODE_INDICATORS:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.debug(f"Get a code indicator found: {indicator}")
                    return True
            except Exception:
                pass

        return False

    async def handle(self, page: Any, credentials: dict[str, str]) -> bool:
        """
        Handle "Get a code" by logging instructions for manual intervention.

        This handler cannot proceed automatically. It logs instructions
        and waits for the configured timeout.

        Args:
            page: Playwright page object
            credentials: Not used for this handler

        Returns:
            False (requires manual intervention)
        """
        self.logger.warning("=== MANUAL INTERVENTION REQUIRED ===")
        self.logger.warning("Microsoft is requesting a verification code via email or SMS.")
        self.logger.warning("Please check your email/phone and enter the code manually.")
        self.logger.warning("The system will wait for the configured timeout period.")

        # Wait for manual intervention timeout
        timeout = self.config.get("login.manual_intervention_timeout", 120)
        self.logger.info(f"Waiting {timeout} seconds for manual intervention...")

        await page.wait_for_timeout(timeout * 1000)

        # Return False to indicate manual intervention needed
        return False

    def get_next_states(self) -> list[LoginState]:
        """
        Possible next states after manual intervention.

        Returns:
            List of possible next states
        """
        return [
            LoginState.LOGGED_IN,
            LoginState.ERROR,
        ]
