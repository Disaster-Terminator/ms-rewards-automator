"""
数据模型定义
使用 dataclasses 定义配置和状态数据结构

注意：此文件中的模型为备用定义。
主要的配置类在 app_config.py 中定义。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DeviceType(Enum):
    """设备类型"""

    DESKTOP_EDGE = "desktop_edge"
    DESKTOP_CHROME = "desktop_chrome"
    MOBILE_IPHONE = "mobile_iphone"
    MOBILE_ANDROID = "mobile_android"


class SearchStatus(Enum):
    """搜索状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SearchConfig:
    """搜索配置"""

    desktop_count: int = 30
    mobile_count: int = 20
    wait_interval_min: int = 8
    wait_interval_max: int = 20
    search_terms_file: str = "tools/search_terms.txt"


@dataclass
class BrowserConfig:
    """浏览器配置"""

    headless: bool = False
    slow_mo: int = 100
    timeout: int = 30000


@dataclass
class AccountConfig:
    """账户配置"""

    storage_state_path: str = "storage_state.json"
    login_url: str = "https://rewards.microsoft.com/"


@dataclass
class AntiDetectionConfig:
    """反检测配置"""

    use_stealth: bool = True
    random_viewport: bool = True
    simulate_human_typing: bool = True
    scroll_enabled: bool = True
    min_scrolls: int = 2
    max_scrolls: int = 5


@dataclass
class MonitoringConfig:
    """监控配置"""

    enabled: bool = True
    check_interval: int = 5
    check_points_before_task: bool = True
    alert_on_no_increase: bool = True
    max_no_increase_count: int = 3


@dataclass
class ErrorHandlingConfig:
    """错误处理配置"""

    max_retries: int = 3
    retry_delay: int = 5
    exponential_backoff: bool = True


@dataclass
class AccountState:
    """账户状态"""

    logged_in: bool = False
    current_points: int | None = None
    desktop_searches_completed: int = 0
    mobile_searches_completed: int = 0
    last_check_time: datetime | None = None
    session_valid: bool = False


@dataclass
class SearchTerm:
    """搜索词"""

    term: str
    used_count: int = 0
    last_used: datetime | None = None
    source: str = "file"


@dataclass
class SearchResult:
    """搜索结果"""

    term: str
    success: bool
    timestamp: datetime
    device_type: DeviceType
    points_before: int | None = None
    points_after: int | None = None
    error_message: str | None = None


@dataclass
class SearchSession:
    """搜索会话"""

    session_id: str
    start_time: datetime
    device_type: DeviceType
    end_time: datetime | None = None
    search_results: list[SearchResult] = field(default_factory=list)
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    points_gained: int = 0
    status: SearchStatus = SearchStatus.PENDING
    error_count: int = 0
    alerts: list[dict] = field(default_factory=list)


@dataclass
class DailyReport:
    """每日报告"""

    date: str
    timestamp: datetime
    desktop_searches: int = 0
    mobile_searches: int = 0
    total_searches: int = 0
    points_start: int | None = None
    points_end: int | None = None
    points_gained: int = 0
    sessions: list[SearchSession] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    status: str = "completed"
    notes: str = ""


@dataclass
class TaskStatus:
    """任务状态"""

    task_type: str
    completed: bool = False
    progress: int = 0
    max_progress: int = 0
    last_updated: datetime | None = None


@dataclass
class RewardsAccount:
    """Rewards 账户信息"""

    email: str | None = None
    current_points: int | None = None
    lifetime_points: int | None = None
    tasks: list[TaskStatus] = field(default_factory=list)
    last_login: datetime | None = None
    session_valid: bool = False
