"""
Login State Machine for Microsoft Account Authentication.

This module implements a finite state machine to handle various Microsoft
login scenarios including email/password input, 2FA, passwordless auth, etc.

Design Pattern: State Machine with Handler Registry
- Enum-based states for type safety
- Handler registry for extensibility
- State history tracking for debugging
- Timeout and max transitions protection
"""

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import logging
import asyncio
import os

from playwright.async_api import Page

from infrastructure.self_diagnosis import SelfDiagnosisSystem
from login.edge_popup_handler import EdgePopupHandler

if TYPE_CHECKING:
    from infrastructure.config_manager import ConfigManager
    from login.state_handler import StateHandler


class LoginState(Enum):
    """
    Enumeration of possible login states.
    
    Each state represents a distinct page or authentication step
    in the Microsoft login flow.
    """
    LOGGED_IN = "logged_in"
    EMAIL_INPUT = "email_input"
    PASSWORD_INPUT = "password_input"
    TOTP_2FA = "totp_2fa"
    PASSWORDLESS = "passwordless"
    GET_A_CODE = "get_a_code"
    OTP_CODE_ENTRY = "otp_code_entry"  # 邮件/短信验证码输入页面
    STAY_SIGNED_IN = "stay_signed_in"  # "保持登录"提示页面
    RECOVERY_EMAIL = "recovery_email"
    MOBILE_ACCESS = "mobile_access"
    AUTH_BLOCKED = "auth_blocked"  # Microsoft 拒绝登录，需要重试
    ERROR = "error"
    
    def __str__(self) -> str:
        return self.value


class StateTransition:
    """Represents a state transition with metadata."""
    
    def __init__(
        self,
        from_state: LoginState,
        to_state: LoginState,
        timestamp: datetime,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = timestamp
        self.success = success
        self.error_message = error_message
    
    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"StateTransition({status} {self.from_state} → {self.to_state} "
            f"at {self.timestamp.strftime('%H:%M:%S')})"
        )


class LoginStateMachine:
    """
    Finite State Machine for handling Microsoft login flows.
    
    This class manages the login process by:
    1. Detecting the current authentication state
    2. Executing appropriate handlers for each state
    3. Tracking state transitions for debugging
    4. Preventing infinite loops with timeouts
    
    Attributes:
        config: Configuration manager instance
        current_state: Current login state
        state_history: List of state transitions
        handlers: Registry of state handlers
        logger: Logger instance
    """
    
    def __init__(self, config: 'ConfigManager', logger: Optional[logging.Logger] = None):
        """
        Initialize the login state machine.
        
        Args:
            config: Configuration manager instance
            logger: Optional logger instance (creates new if not provided)
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        self.current_state = LoginState.ERROR
        self._max_history_size = 50
        self.state_history: deque = deque(maxlen=self._max_history_size)
        
        self.handlers: Dict[LoginState, 'StateHandler'] = {}
        
        self.max_transitions = config.get("login.max_transitions", 10)
        self.timeout_seconds = config.get("login.timeout_seconds", 300)
        
        self.diagnosis_system: Optional[SelfDiagnosisSystem] = None
        
        self.edge_popup_handler = EdgePopupHandler(logger=self.logger)
        
        self.logger.info(
            f"LoginStateMachine initialized "
            f"(max_transitions={self.max_transitions}, "
            f"timeout={self.timeout_seconds}s)"
        )
    
    def register_handler(self, state: LoginState, handler: 'StateHandler') -> None:
        """
        Register a handler for a specific state.
        
        Args:
            state: The login state this handler manages
            handler: Handler instance implementing StateHandler interface
        """
        self.handlers[state] = handler
        self.logger.debug(f"Registered handler for state: {state}")
    
    async def detect_state(self, page: Page) -> LoginState:
        """
        Detect the current login state by examining page elements.
        
        This method checks the page for specific selectors and patterns
        to determine which authentication state we're in.
        
        Priority order:
        1. LOGGED_IN - highest priority
        2. TOTP_2FA - must check before PASSWORDLESS (can have similar text)
        3. PASSWORD_INPUT
        4. PASSWORDLESS
        5. EMAIL_INPUT
        6. Others
        
        Args:
            page: Playwright page object
            
        Returns:
            Detected LoginState
        """
        self.logger.debug("Detecting login state...")
        
        # Define priority order for state detection
        priority_order = [
            LoginState.LOGGED_IN,
            LoginState.AUTH_BLOCKED,  # Check early to handle blocks quickly
            LoginState.STAY_SIGNED_IN,  # Check before TOTP_2FA (can appear after 2FA)
            LoginState.TOTP_2FA,  # Must check before PASSWORDLESS and OTP_CODE_ENTRY
            LoginState.OTP_CODE_ENTRY,  # Check before PASSWORDLESS
            LoginState.PASSWORD_INPUT,
            LoginState.PASSWORDLESS,
            LoginState.EMAIL_INPUT,
            LoginState.GET_A_CODE,
            LoginState.RECOVERY_EMAIL,
            LoginState.MOBILE_ACCESS,
        ]
        
        # Check handlers in priority order
        for state in priority_order:
            handler = self.handlers.get(state)
            if handler and await handler.can_handle(page):
                self.logger.info(f"Detected state: {state}")
                return state
        
        # If no handler matches, return ERROR state
        self.logger.warning("Could not detect login state, returning ERROR")
        return LoginState.ERROR

    
    def _record_transition(
        self,
        from_state: LoginState,
        to_state: LoginState,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record a state transition in history.
        
        Args:
            from_state: State we're transitioning from
            to_state: State we're transitioning to
            success: Whether the transition was successful
            error_message: Optional error message if transition failed
        """
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message
        )
        
        self.state_history.append(transition)
        
        # Log the transition
        if success:
            self.logger.info(f"State transition: {from_state} → {to_state}")
        else:
            self.logger.error(
                f"Failed transition: {from_state} → {to_state} "
                f"({error_message})"
            )
    
    def get_state_history(self) -> List[StateTransition]:
        """
        Get the complete state transition history.
        
        Returns:
            List of StateTransition objects
        """
        return list(self.state_history)
    
    def get_transition_count(self) -> int:
        """
        Get the number of state transitions that have occurred.
        
        Returns:
            Number of transitions
        """
        return len(self.state_history)
    
    def reset(self) -> None:
        """
        Reset the state machine to initial state.
        
        Clears state history and resets current state to ERROR.
        """
        self.logger.info("Resetting state machine")
        self.current_state = LoginState.ERROR
        self.state_history.clear()
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        Get diagnostic information about the state machine.
        
        Useful for debugging and error reporting.
        
        Returns:
            Dictionary containing diagnostic information
        """
        return {
            "current_state": str(self.current_state),
            "transition_count": self.get_transition_count(),
            "max_transitions": self.max_transitions,
            "timeout_seconds": self.timeout_seconds,
            "registered_handlers": [str(state) for state in self.handlers.keys()],
            "state_history": [
                {
                    "from": str(t.from_state),
                    "to": str(t.to_state),
                    "timestamp": t.timestamp.isoformat(),
                    "success": t.success,
                    "error": t.error_message
                }
                for t in self.state_history
            ]
        }

    
    async def handle_login(
        self,
        page: Page,
        credentials: Dict[str, str],
        max_transitions: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Execute the login flow by transitioning through states.
        
        This is the main entry point for the login process. It:
        1. Detects the current state
        2. Executes the appropriate handler
        3. Transitions to the next state
        4. Repeats until logged in or error
        
        Args:
            page: Playwright page object
            credentials: Dictionary containing login credentials
                        (email, password, totp_secret, etc.)
            max_transitions: Override default max transitions
            timeout: Override default timeout in seconds
            
        Returns:
            True if login successful, False otherwise
            
        Raises:
            TimeoutError: If login exceeds timeout
            RuntimeError: If max transitions exceeded
        """
        max_trans = max_transitions or self.max_transitions
        timeout_sec = timeout or self.timeout_seconds
        
        # Initialize diagnosis system
        self.diagnosis_system = SelfDiagnosisSystem(page)
        
        self.logger.info(
            f"Starting login flow (max_transitions={max_trans}, "
            f"timeout={timeout_sec}s)"
        )
        
        start_time = datetime.now()
        transition_count = 0
        same_state_count = 0  # 防卡死：追踪同一状态的连续次数
        
        while True:
            # 注意：不再调用 EdgePopupHandler，因为使用 chromium 不会有 Edge 弹窗
            # 如果使用 Edge 浏览器，EdgePopupHandler 的选择器太宽泛会误点其他按钮
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout_sec:
                self.logger.error(f"Login timeout after {elapsed:.1f}s")
                raise TimeoutError(
                    f"Login exceeded timeout of {timeout_sec}s"
                )
            
            # Check max transitions
            if transition_count >= max_trans:
                self.logger.error(
                    f"Max transitions ({max_trans}) exceeded"
                )
                raise RuntimeError(
                    f"Login exceeded maximum transitions ({max_trans})"
                )
            
            # Detect current state (with timeout monitoring)
            try:
                previous_state = self.current_state

                # 确保页面完全加载（使用宽松策略，避免 networkidle 永久等待）
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await page.wait_for_selector("body", timeout=10000)
                    await page.wait_for_load_state("load", timeout=15000)  # 改用 load 替代 networkidle
                except Exception as e:
                    # 即使超时也继续，因为实际操作可能已经成功
                    self.logger.debug(f"页面加载检查: {e}")

                self.current_state = await self.diagnosis_system.monitor_execution(
                    lambda: self.detect_state(page),
                    timeout=60,  # 增加到 60 秒，因为需要检查多个 handler
                    operation_name=f"Detect state (from {previous_state})"
                )
            except TimeoutError as e:
                self.logger.error(f"State detection timeout: {e}")
                self.current_state = LoginState.ERROR
                return False
            
            # Record transition if state changed
            if previous_state != self.current_state:
                self._record_transition(previous_state, self.current_state)
                transition_count += 1
                same_state_count = 0  # 重置同状态计数
            else:
                # 防卡死机制：检测是否卡在同一状态
                if self.current_state != LoginState.LOGGED_IN:
                    same_state_count += 1
                    self.logger.warning(
                        f"卡在同一状态 {self.current_state}，"
                        f"连续 {same_state_count} 次"
                    )
                    
                    if same_state_count >= 4:
                        self.logger.error(
                            f"卡在 {self.current_state} 状态 4 次，"
                            f"刷新页面重试"
                        )
                        
                        # 保存诊断 HTML
                        try:
                            os.makedirs("logs/diagnostics", exist_ok=True)
                            html_content = await page.content()
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            html_path = f"logs/diagnostics/stuck_{self.current_state}_{timestamp}.html"
                            with open(html_path, "w", encoding="utf-8") as f:
                                f.write(html_content)
                            self.logger.info(f"已保存卡死状态 HTML: {html_path}")
                        except Exception as e:
                            self.logger.debug(f"保存 HTML 失败: {e}")
                        
                        # 刷新页面
                        await page.reload(wait_until="domcontentloaded")
                        same_state_count = 0
                        self.current_state = LoginState.ERROR  # 强制重新检测
                        await page.wait_for_timeout(2000)
                        continue
            
            # Check if we're logged in
            if self.current_state == LoginState.LOGGED_IN:
                self.logger.info(
                    f"Login successful after {transition_count} transitions "
                    f"in {elapsed:.1f}s"
                )
                return True
            
            # Check if we're in error state
            if self.current_state == LoginState.ERROR:
                self.logger.error("Login failed: ERROR state detected")
                
                # 保存诊断 HTML
                try:
                    os.makedirs("logs/diagnostics", exist_ok=True)
                    html_content = await page.content()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    html_path = f"logs/diagnostics/error_state_{timestamp}.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    self.logger.error(f"ERROR 状态 HTML 已保存: {html_path}")
                    
                    # 同时保存截图
                    screenshot_path = f"logs/diagnostics/error_state_{timestamp}.png"
                    await page.screenshot(path=screenshot_path)
                    self.logger.error(f"ERROR 状态截图已保存: {screenshot_path}")
                except Exception as e:
                    self.logger.debug(f"保存诊断信息失败: {e}")
                
                self._record_transition(
                    previous_state,
                    LoginState.ERROR,
                    success=False,
                    error_message="Unrecognized page state"
                )
                return False
            
            # Get handler for current state
            handler = self.handlers.get(self.current_state)
            if not handler:
                self.logger.error(
                    f"No handler registered for state: {self.current_state}"
                )
                self.current_state = LoginState.ERROR
                self._record_transition(
                    previous_state,
                    LoginState.ERROR,
                    success=False,
                    error_message=f"No handler for {self.current_state}"
                )
                return False
            
            # Execute handler (with timeout monitoring)
            try:
                self.logger.debug(
                    f"Executing handler for state: {self.current_state}"
                )
                
                success = await self.diagnosis_system.monitor_execution(
                    lambda: handler.handle(page, credentials),
                    timeout=60,
                    operation_name=f"Handle state: {self.current_state}"
                )
                
                if not success:
                    self.logger.warning(
                        f"Handler for {self.current_state} returned False"
                    )
                    # Continue anyway - next iteration will detect new state
                
            except TimeoutError as e:
                self.logger.error(f"Handler timeout: {e}")
                self.current_state = LoginState.ERROR
                self._record_transition(
                    previous_state,
                    LoginState.ERROR,
                    success=False,
                    error_message=f"Handler timeout: {e}"
                )
                return False
            except Exception as e:
                self.logger.error(
                    f"Handler for {self.current_state} raised exception: {e}",
                    exc_info=True
                )
                self.current_state = LoginState.ERROR
                self._record_transition(
                    previous_state,
                    LoginState.ERROR,
                    success=False,
                    error_message=str(e)
                )
                return False
            
            # Small delay to allow page to update
            await page.wait_for_timeout(1000)
