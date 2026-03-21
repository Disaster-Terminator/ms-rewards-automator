"""
配置类型定义模块

提供类型安全的配置字典，用于 ConfigManager 的 config 属性。
使用 TypedDict 而非 dataclass 以保持动态配置灵活性。
"""

from typing import Any, TypedDict


class SearchWaitInterval(TypedDict):
    """搜索等待间隔配置"""

    min: float
    max: float


class SearchConfig(TypedDict):
    """搜索配置"""

    desktop_count: int
    mobile_count: int
    wait_interval: SearchWaitInterval
    search_terms_file: str


class BrowserConfig(TypedDict):
    """浏览器配置"""

    headless: bool
    prevent_focus: str  # "basic", "enhanced", "none"
    slow_mo: int
    timeout: int
    type: str  # "chromium", "chrome", "edge"


class AccountConfig(TypedDict, total=False):
    """账户配置（可选字段使用 total=False）"""

    storage_state_path: str
    login_url: str
    email: str
    password: str
    totp_secret: str


class AutoLoginConfig(TypedDict):
    """自动登录配置"""

    enabled: bool
    email: str
    password: str
    totp_secret: str


class LoginConfig(TypedDict):
    """登录配置"""

    state_machine_enabled: bool
    max_transitions: int
    timeout_seconds: int
    stay_signed_in: bool
    manual_intervention_timeout: int
    auto_login: AutoLoginConfig


class QuerySourcesConfig(TypedDict):
    """查询源配置"""

    local_file: dict[str, bool]
    bing_suggestions: dict[str, bool]
    duckduckgo: dict[str, bool]
    wikipedia: dict[str, bool]


class BingAPIConfig(TypedDict):
    """Bing API 配置"""

    rate_limit: int
    max_retries: int
    timeout: int
    suggestions_per_query: int
    suggestions_per_seed: int
    max_expand: int


class QueryEngineConfig(TypedDict):
    """查询引擎配置"""

    enabled: bool
    cache_ttl: int
    sources: QuerySourcesConfig
    bing_api: BingAPIConfig


class TaskTypesConfig(TypedDict):
    """任务类型配置"""

    url_reward: bool
    quiz: bool
    poll: bool


class TaskParserConfig(TypedDict):
    """任务解析器配置"""

    skip_hrefs: list[str]
    skip_text_patterns: list[str]
    completed_text_patterns: list[str]
    points_selector: str
    completed_circle_class: str
    incomplete_circle_class: str
    login_selectors: list[str]
    earn_link_selector: str


class TaskSystemConfig(TypedDict):
    """任务系统配置"""

    enabled: bool
    min_delay: int
    max_delay: int
    skip_completed: bool
    debug_mode: bool
    task_types: TaskTypesConfig
    task_parser: TaskParserConfig


class BingThemeConfig(TypedDict):
    """Bing 主题配置"""

    enabled: bool
    theme: str  # "dark", "light"
    force_theme: bool
    persistence_enabled: bool
    theme_state_file: str


class HealthCheckConfig(TypedDict):
    """健康检查配置"""

    enabled: bool
    interval: int
    save_reports: bool


class MonitoringConfig(TypedDict):
    """监控配置"""

    enabled: bool
    check_interval: int
    check_points_before_task: bool
    alert_on_no_increase: bool
    max_no_increase_count: int
    real_time_display: bool
    health_check: HealthCheckConfig


class TelegramConfig(TypedDict):
    """Telegram 通知配置"""

    enabled: bool
    bot_token: str
    chat_id: str


class ServerChanConfig(TypedDict):
    """Server酱通知配置"""

    enabled: bool
    key: str


class WhatsAppConfig(TypedDict):
    """WhatsApp 通知配置"""

    enabled: bool
    phone: str
    apikey: str


class NotificationConfig(TypedDict):
    """通知配置"""

    enabled: bool
    telegram: TelegramConfig
    serverchan: ServerChanConfig
    whatsapp: WhatsAppConfig


class SchedulerConfig(TypedDict):
    """调度器配置（简化版：仅支持 scheduled 模式）"""

    enabled: bool
    mode: str  # 保留配置但实际只支持 "scheduled"
    scheduled_hour: int
    max_offset_minutes: int
    timezone: str
    run_once_on_start: bool
    # 注意：random_start_hour, random_end_hour, fixed_hour, fixed_minute 已移除（未使用）


class ErrorHandlingConfig(TypedDict):
    """错误处理配置"""

    max_retries: int
    retry_delay: int
    exponential_backoff: bool


class LoggingConfig(TypedDict):
    """日志配置"""

    level: str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    file: str
    console: bool


class ExecutionConfig(TypedDict):
    """执行模式配置"""

    mode: str  # "fast", "normal", "slow"


class AntiDetectionConfig(TypedDict):
    """反检测配置"""

    use_stealth: bool
    random_viewport: bool
    human_behavior_level: str
    scroll_behavior: dict[str, Any]
    mouse_movement: dict[str, Any]
    typing: dict[str, Any]


class ConfigDict(TypedDict):
    """
    完整配置字典类型

    根配置结构，包含所有配置节。
    所有字段都是必需的（在通过 DEFAULT_CONFIG 合并后）。
    """

    execution: ExecutionConfig
    search: SearchConfig
    browser: BrowserConfig
    account: AccountConfig
    login: LoginConfig
    query_engine: QueryEngineConfig
    task_system: TaskSystemConfig
    bing_theme: BingThemeConfig
    monitoring: MonitoringConfig
    notification: NotificationConfig
    scheduler: SchedulerConfig
    anti_detection: AntiDetectionConfig
    error_handling: ErrorHandlingConfig
    logging: LoggingConfig
