"""
Password Input Handler.

Handles the password input state in Microsoft login flow.
"""

from typing import List, Dict
from playwright.async_api import Page
from ..state_handler import StateHandler
from ..login_state_machine import LoginState
from ..edge_popup_handler import EdgePopupHandler


class PasswordInputHandler(StateHandler):
    """
    Handler for password input state.
    
    This handler:
    1. Detects the password input page
    2. Fills in the password
    3. Clicks the "Sign in" button
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize handler with Edge popup handler."""
        super().__init__(*args, **kwargs)
        self.edge_popup_handler = EdgePopupHandler(logger=self.logger)
    
    # Common selectors for password input
    PASSWORD_INPUT_SELECTORS = [
        'input[type="password"]',
        'input[name="passwd"]',
        'input[id="i0118"]',
    ]
    
    SIGNIN_BUTTON_SELECTORS = [
        'input[type="submit"]',
        'input[id="idSIButton9"]',
        'button[type="submit"]',
    ]
    
    # "Stay signed in?" prompt selectors
    STAY_SIGNED_IN_YES = [
        'input[id="idSIButton9"]',
        'button:has-text("Yes")',
    ]
    
    STAY_SIGNED_IN_NO = [
        'input[id="idBtn_Back"]',
        'button:has-text("No")',
    ]
    
    async def can_handle(self, page: Page) -> bool:
        """
        Check if current page is the password input page.

        Args:
            page: Playwright page object

        Returns:
            True if password input page detected
        """
        # 快速检查：先检查 URL
        url = page.url.lower()
        if "login" not in url and "microsoft" not in url:
            return False

        # Check for password input field (reduced timeout for speed)
        for selector in self.PASSWORD_INPUT_SELECTORS:
            if await self.element_exists(page, selector, timeout=1000):
                self.logger.debug(f"Password input detected: {selector}")
                return True

        return False
    
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """
        Handle password input by filling password and clicking sign in.
        
        Args:
            page: Playwright page object
            credentials: Must contain 'password' key
            
        Returns:
            True if successful
        """
        password = credentials.get('password')
        if not password:
            self.logger.error("No password provided in credentials")
            return False
        
        self.logger.info("Handling password input")
        
        # 首先尝试关闭可能的 Edge 弹窗
        await self.edge_popup_handler.dismiss_popup(page)
        
        # Small delay before interaction (simulate reading the page)
        await self.human_simulator.human_delay(600, 1200)
        
        # Find and fill password input with human-like typing
        filled = False
        password_selector_used = None
        for selector in self.PASSWORD_INPUT_SELECTORS:
            if await self.safe_fill(page, selector, password, timeout=5000, human_like=True):
                filled = True
                password_selector_used = selector
                break
        
        if not filled:
            self.logger.error("Failed to fill password input")
            return False
        
        self.logger.debug(f"Password filled using selector: {password_selector_used}")
        
        # Delay after typing (simulate checking password)
        await self.human_simulator.human_delay(800, 1500)
        
        # Check current URL before clicking
        current_url = page.url
        self.logger.debug(f"Current URL after password fill: {current_url}")
        
        # Click sign in button with human-like behavior
        clicked = False
        for selector in self.SIGNIN_BUTTON_SELECTORS:
            if await self.safe_click(page, selector, timeout=5000, human_like=True):
                clicked = True
                self.logger.info(f"✓ Successfully clicked: {selector}")
                break
        
        if not clicked:
            self.logger.warning("All sign-in button selectors failed")
            self.logger.info("Checking if page auto-submitted after password fill...")
            # 等待看是否自动跳转
            await page.wait_for_timeout(2000)
            new_url = page.url
            if new_url != current_url:
                self.logger.info(f"✓ Page auto-submitted: {current_url} → {new_url}")
            else:
                self.logger.error("Page did not auto-submit and button click failed")
                return False
        
        # 等待页面跳转完成（重要：给足够时间让页面跳转）
        self.logger.debug("Waiting for page navigation after sign-in...")
        await page.wait_for_timeout(3000)  # 增加等待时间
        
        # Handle "Stay signed in?" prompt if it appears
        # 注意：这个提示可能需要几秒才出现，所以要有足够的等待
        await self._handle_stay_signed_in_prompt(page)
        
        self.logger.info("Password input handled successfully")
        return True
    
    async def _handle_stay_signed_in_prompt(self, page: Page) -> None:
        """
        Handle the "Stay signed in?" prompt if it appears.
        
        Args:
            page: Playwright page object
        """
        # 等待提示出现（最多 5 秒）
        self.logger.debug("Checking for 'Stay signed in?' prompt...")
        await page.wait_for_timeout(2000)  # 先等待 2 秒让提示出现
        
        # Check if prompt exists
        stay_signed_in_config = self.config.get("login.stay_signed_in", True)
        
        if stay_signed_in_config:
            # Click "Yes"
            for selector in self.STAY_SIGNED_IN_YES:
                if await self.safe_click(page, selector, timeout=3000, human_like=True):
                    self.logger.info("✓ Clicked 'Yes' on stay signed in prompt")
                    await page.wait_for_timeout(2000)  # 等待跳转
                    return
            
            self.logger.debug("'Stay signed in?' prompt not found (may have auto-proceeded)")
        else:
            # Click "No"
            for selector in self.STAY_SIGNED_IN_NO:
                if await self.safe_click(page, selector, timeout=3000, human_like=True):
                    self.logger.info("✓ Clicked 'No' on stay signed in prompt")
                    await page.wait_for_timeout(2000)  # 等待跳转
                    return
            
            self.logger.debug("'Stay signed in?' prompt not found (may have auto-proceeded)")
    
    def get_next_states(self) -> List[LoginState]:
        """
        Possible next states after password input.
        
        Returns:
            List of possible next states
        """
        return [
            LoginState.LOGGED_IN,
            LoginState.TOTP_2FA,
            LoginState.GET_A_CODE,
            LoginState.RECOVERY_EMAIL,
            LoginState.ERROR,
        ]
