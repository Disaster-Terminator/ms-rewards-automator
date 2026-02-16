"""
Logged In Handler.

Detects when user is successfully logged in.
"""

from typing import List, Dict
from playwright.async_api import Page
from ..state_handler import StateHandler
from ..login_state_machine import LoginState


class LoggedInHandler(StateHandler):
    """
    Handler for logged in state detection.
    
    This handler checks if the user is already logged in
    by looking for Microsoft account indicators.
    """
    
    # Selectors that indicate logged in state
    LOGGED_IN_INDICATORS = [
        'a[id="mectrl_currentAccount_primary"]',
        'button[id="mectrl_headerPicture"]',
        'div[id="meControl"]',
        'text=Sign out',
    ]
    
    # URLs that indicate logged in state
    LOGGED_IN_URLS = [
        'rewards.bing.com',
        'account.microsoft.com',
        'bing.com',
    ]
    
    # OAuth callback URLs (login completed, waiting for redirect)
    OAUTH_CALLBACK_URLS = [
        'complete-client-signin',
        'complete-sso-with-redirect',
        'oauth-silent',
        'oauth20',  # 通用 OAuth 回调路径（例如 oauth20_authorize.srf 等）
    ]
    
    async def can_handle(self, page: Page) -> bool:
        """
        Check if user is logged in.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if logged in detected
        """
        # Check URL
        current_url = page.url
        
        # Check for OAuth callback URLs (login completed, waiting for redirect)
        for oauth_pattern in self.OAUTH_CALLBACK_URLS:
            if oauth_pattern in current_url:
                self.logger.info(f"检测到 OAuth 回调页面: {oauth_pattern}")
                self.logger.info("登录已完成，等待页面自动跳转...")
                return True
        
        # Check for normal logged in URLs
        for url_pattern in self.LOGGED_IN_URLS:
            if url_pattern in current_url:
                # Check for logged in indicators
                for selector in self.LOGGED_IN_INDICATORS:
                    if await self.element_exists(page, selector, timeout=2000):
                        self.logger.debug(f"Logged in indicator found: {selector}")
                        return True
        
        return False
    
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """
        Handle logged in state (no action needed).
        
        Args:
            page: Playwright page object
            credentials: Not used
            
        Returns:
            True (already logged in)
        """
        self.logger.info("User is already logged in")
        return True
    
    def get_next_states(self) -> List[LoginState]:
        """
        No next states (terminal state).
        
        Returns:
            Empty list
        """
        return []
