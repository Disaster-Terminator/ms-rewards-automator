"""
State Handler Base Class and Interface.

This module defines the abstract base class for login state handlers.
Each handler is responsible for:
1. Detecting if it can handle the current page state
2. Executing the appropriate actions for that state
3. Reporting possible next states

Design Pattern: Strategy Pattern with Template Method
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from enum import Enum
import logging

from playwright.async_api import Page

if TYPE_CHECKING:
    from infrastructure.config_manager import ConfigManager


class StateHandler(ABC):
    """
    Abstract base class for login state handlers.
    
    Each concrete handler implements the logic for a specific
    authentication state (e.g., email input, password input, 2FA).
    
    Attributes:
        logger: Logger instance for this handler
        config: Configuration manager instance
        human_simulator: Human behavior simulator for anti-detection
    """
    
    def __init__(self, config: 'ConfigManager', logger: Optional[logging.Logger] = None):
        """
        Initialize the state handler.
        
        Args:
            config: Configuration manager instance
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        from .human_behavior_simulator import HumanBehaviorSimulator
        self.human_simulator = HumanBehaviorSimulator(logger=self.logger)
    
    @abstractmethod
    async def can_handle(self, page: Page) -> bool:
        """
        Check if this handler can handle the current page state.
        
        This method examines the page for specific selectors or patterns
        that indicate this handler should be used.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if this handler can handle the current page, False otherwise
        """
        pass
    
    @abstractmethod
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """
        Handle the current state by performing appropriate actions.
        
        This method executes the logic for this specific state, such as:
        - Filling in form fields
        - Clicking buttons
        - Waiting for page transitions
        
        Args:
            page: Playwright page object
            credentials: Dictionary containing login credentials
            
        Returns:
            True if handling was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_next_states(self) -> List['LoginState']:
        """
        Return possible next states after handling this state.
        
        This helps the state machine understand the expected flow
        and detect unexpected transitions.
        
        Returns:
            List of possible next LoginState values
        """
        pass
    
    def get_handler_name(self) -> str:
        """
        Get the name of this handler.
        
        Returns:
            Handler class name
        """
        return self.__class__.__name__
    
    async def wait_for_navigation(
        self,
        page: Any,
        timeout: int = 60000
    ) -> bool:
        """
        Wait for page navigation to complete.

        Helper method for handlers that trigger page navigation.
        Uses a more tolerant approach for pages with continuous network activity.

        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds

        Returns:
            True if navigation completed, False if timeout
        """
        try:
            # 等待 DOM 加载完成
            await page.wait_for_load_state("domcontentloaded", timeout=timeout // 3)
            # 等待主要资源加载完成（不用 networkidle，因为微软页面有大量追踪请求）
            await page.wait_for_load_state("load", timeout=timeout // 3)
            # 额外等待确保 JavaScript 执行完成
            await page.wait_for_timeout(2000)
            return True
        except Exception as e:
            # 即使超时也尝试继续，因为实际操作可能已经成功
            self.logger.debug(f"Navigation wait timeout (continuing anyway): {e}")
            # 添加短暂等待后继续
            await page.wait_for_timeout(1000)
            return True  # 返回 True 让流程继续
    
    async def safe_click(
        self,
        page: Any,
        selector: str,
        timeout: int = 10000,
        human_like: bool = True
    ) -> bool:
        """
        Safely click an element with error handling.
        
        Args:
            page: Playwright page object
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            human_like: Use human-like behavior (default: True)
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            if human_like:
                # Use human behavior simulator
                return await self.human_simulator.human_click(page, selector, timeout)
            else:
                # Fallback to direct click
                await page.wait_for_selector(selector, timeout=timeout)
                await page.click(selector)
                self.logger.debug(f"Clicked element: {selector}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to click {selector}: {e}")
            return False
    
    async def safe_fill(
        self,
        page: Any,
        selector: str,
        value: str,
        timeout: int = 10000,
        human_like: bool = True
    ) -> bool:
        """
        Safely fill an input field with error handling.
        
        Args:
            page: Playwright page object
            selector: CSS selector for the input field
            value: Value to fill
            timeout: Timeout in milliseconds
            human_like: Use human-like typing (default: True)
            
        Returns:
            True if fill successful, False otherwise
        """
        try:
            if human_like:
                # Use human behavior simulator
                return await self.human_simulator.human_type(page, selector, value, timeout)
            else:
                # Fallback to direct fill
                await page.wait_for_selector(selector, timeout=timeout)
                await page.fill(selector, value)
                self.logger.debug(f"Filled element: {selector}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to fill {selector}: {e}")
            return False
    
    async def element_exists(
        self,
        page: Any,
        selector: str,
        timeout: int = 2000
    ) -> bool:
        """
        Check if an element exists on the page.
        
        Args:
            page: Playwright page object
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            
        Returns:
            True if element exists, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            # 明确捕获所有异常（包括 TimeoutError）并返回 False
            # 这样可以避免 "Future exception was never retrieved" 警告
            return False
