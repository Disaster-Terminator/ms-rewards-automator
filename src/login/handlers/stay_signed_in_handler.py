"""
Stay Signed In Handler.

Handles the "Stay signed in?" prompt after successful authentication.
"""

from typing import List, Dict
from playwright.async_api import Page
from ..state_handler import StateHandler
from ..login_state_machine import LoginState


class StaySignedInHandler(StateHandler):
    """
    Handler for "Stay signed in?" prompt.
    
    This handler:
    1. Detects the KMSI (Keep Me Signed In) page
    2. Clicks "Yes" to save login state
    3. Waits for redirect to complete
    """
    
    # Selectors for the "Yes" button
    YES_BUTTON_SELECTORS = [
        'button[data-testid="primaryButton"]',  # Fluent UI primary button
        'button:has-text("Yes")',
        'input[type="submit"][value="Yes"]',
        'button[id="idSIButton9"]',  # Legacy selector
    ]
    
    # Page indicators
    KMSI_PAGE_INDICATORS = [
        'text=Stay signed in?',
        'text=保持登录状态',
        'h1:has-text("Stay signed in")',
        '[data-testid="kmsiVideo"]',  # Video element on KMSI page
        '[data-testid="kmsiImage"]',  # Image fallback
    ]
    
    async def can_handle(self, page: Page) -> bool:
        """
        Check if current page is the "Stay signed in?" page.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if KMSI page detected
        """
        # Check URL
        current_url = page.url
        if 'kmsi' in current_url.lower():
            self.logger.debug("KMSI page detected by URL")
            return True
        
        # Check title
        try:
            title = await page.title()
            if title and 'stay signed in' in title.lower():
                self.logger.debug(f"KMSI page detected by title: {title}")
                return True
        except Exception:
            pass
        
        # Check page indicators
        for indicator in self.KMSI_PAGE_INDICATORS:
            try:
                element = await page.query_selector(indicator)
                if element:
                    self.logger.debug(f"KMSI page indicator found: {indicator}")
                    return True
            except Exception:
                pass
        
        return False
    
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """
        Handle "Stay signed in?" prompt by clicking Yes.
        
        Args:
            page: Playwright page object
            credentials: Not used
            
        Returns:
            True if successful
        """
        self.logger.info("处理'保持登录'提示")
        
        # Small delay to simulate reading the prompt
        await self.human_simulator.human_delay(800, 1500)
        
        # Click "Yes" button with human-like behavior
        clicked = False
        for selector in self.YES_BUTTON_SELECTORS:
            if await self.safe_click(page, selector, timeout=5000, human_like=True):
                clicked = True
                self.logger.info(f"✓ 已点击'Yes'按钮: {selector}")
                break
        
        if not clicked:
            self.logger.error("无法点击'Yes'按钮")
            return False
        
        # Wait for navigation
        await self.wait_for_navigation(page)
        
        self.logger.info("'保持登录'处理完成")
        return True
    
    def get_next_states(self) -> List[LoginState]:
        """
        Possible next states after KMSI.
        
        Returns:
            List of possible next states
        """
        return [
            LoginState.LOGGED_IN,
            LoginState.ERROR,
        ]
