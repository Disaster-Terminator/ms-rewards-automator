"""
Type definitions module - 简化版

Centralized definition of Protocols used across the project
for improved type safety and IDE support.
"""

from typing import Any, Protocol

from playwright.async_api import Page


class ConfigProtocol(Protocol):
    """Configuration manager protocol - 实际被 account/manager.py 使用"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...

    def get_with_env(self, key: str, env_var: str, default: Any = None) -> Any:
        """Get configuration value with environment variable fallback"""
        ...


class StateHandlerProtocol(Protocol):
    """State handler protocol for login flow - 实际被 login handlers 使用"""

    async def can_handle(self, page: Page) -> bool:
        """Check if this handler can handle the current state"""
        ...

    async def handle(self, page: Page, credentials: dict[str, str]) -> bool:
        """Handle the current state"""
        ...
