"""
Type definitions module

Centralized definition of Protocols and TypedDicts used across the project
for improved type safety and IDE support.
"""

from typing import Protocol, TypedDict, List, Dict, Any, Optional
from playwright.async_api import Page, BrowserContext


class ConfigProtocol(Protocol):
    """Configuration manager protocol"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...


class StateHandlerProtocol(Protocol):
    """State handler protocol for login flow"""
    
    async def can_handle(self, page: Page) -> bool:
        """Check if this handler can handle the current state"""
        ...
    
    async def handle(self, page: Page, credentials: Dict[str, str]) -> bool:
        """Handle the current state"""
        ...


class HealthCheckResult(TypedDict):
    """Health check result structure"""
    status: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_status: str
    issues: List[str]
    timestamp: str


class DetectionInfo(TypedDict):
    """Login detection information"""
    current_state: str
    confidence: float
    detected_selectors: List[str]
    page_url: str
    timestamp: str


class DiagnosticInfo(TypedDict):
    """State machine diagnostic information"""
    current_state: str
    transition_count: int
    max_transitions: int
    timeout_seconds: int
    registered_handlers: List[str]
    state_history: List[Dict[str, Any]]


class TaskDetail(TypedDict):
    """Task detail structure"""
    id: str
    name: str
    points: int
    status: str
    url: Optional[str]
