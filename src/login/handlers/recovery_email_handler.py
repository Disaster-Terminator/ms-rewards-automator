"""
Recovery Email Handler.

Handles the recovery email verification that requires manual intervention.
"""

from typing import List, Dict
from playwright.async_api import Page
from ..state_handler import StateHandler
from ..login_state_machine import LoginState


class RecoveryEmailHandler(StateHandler):
    """
    Handler for recovery email verification state.
    
    This handler detects the recovery email page and logs
    instructions for manual intervention. It cannot proceed
    automatically as it requires user to check email.
    """
    
    # Selectors for recovery email page
    RECOVERY_EMAIL_INDICATORS = [
        'text=Verify your recovery email',
        'text=Help us protect your account',
        'text=recovery email',
    ]
    
    async def can_handle(self, page: Page) -> bool:
        """
        Check if current page is recovery email page.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if recovery email page detected
        """
        for indicator in self.RECOVERY_EMAIL_INDICATORS:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.debug(f"Recovery email indicator found: {indicator}")
                    return True
            except Exception:
                pass
        
        return False
    
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """
        Handle recovery email by logging instructions for manual intervention.
        
        This handler cannot proceed automatically. It logs instructions
        and waits for the configured timeout.
        
        Args:
            page: Playwright page object
            credentials: Not used for this handler
            
        Returns:
            False (requires manual intervention)
        """
        self.logger.warning(
            "=== MANUAL INTERVENTION REQUIRED ==="
        )
        self.logger.warning(
            "Microsoft is requesting recovery email verification."
        )
        self.logger.warning(
            "Please check your recovery email and follow the instructions."
        )
        self.logger.warning(
            "The system will wait for the configured timeout period."
        )
        
        # Wait for manual intervention timeout
        timeout = self.config.get("login.manual_intervention_timeout", 120)
        self.logger.info(f"Waiting {timeout} seconds for manual intervention...")
        
        await page.wait_for_timeout(timeout * 1000)
        
        # Return False to indicate manual intervention needed
        return False
    
    def get_next_states(self) -> List[LoginState]:
        """
        Possible next states after manual intervention.
        
        Returns:
            List of possible next states
        """
        return [
            LoginState.LOGGED_IN,
            LoginState.ERROR,
        ]
