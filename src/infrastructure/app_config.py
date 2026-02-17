"""
AppConfig - 类型化配置模型

使用 dataclass 提供类型安全的配置访问。
支持嵌套配置访问、默认值和配置验证。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchConfig:
    """搜索配置"""

    desktop_count: int = 30
    mobile_count: int = 20
    wait_interval_min: int = 5
    wait_interval_max: int = 15
    search_terms_file: str = "tools/search_terms.txt"


@dataclass
class BrowserConfig:
    """浏览器配置"""

    headless: bool = False
    prevent_focus: str = "basic"  # basic, enhanced, none
    slow_mo: int = 100
    timeout: int = 30000
    type: str = "chromium"  # chromium(Playwright内置,推荐), chrome(系统), edge(系统)


@dataclass
class AccountConfig:
    """账户配置"""

    storage_state_path: str = "storage_state.json"
    login_url: str = "https://rewards.microsoft.com/"
    email: str = ""
    password: str = ""
    totp_secret: str = ""


@dataclass
class AutoLoginConfig:
    """自动登录配置"""

    enabled: bool = False
    email: str = ""
    password: str = ""
    totp_secret: str = ""


@dataclass
class LoginConfig:
    """登录配置"""

    state_machine_enabled: bool = True
    max_transitions: int = 20
    timeout_seconds: int = 300
    stay_signed_in: bool = True
    manual_intervention_timeout: int = 120
    auto_login: AutoLoginConfig = field(default_factory=AutoLoginConfig)


@dataclass
class QuerySourcesConfig:
    """查询源配置"""

    local_file: dict[str, bool] = field(default_factory=lambda: {"enabled": True})
    bing_suggestions: dict[str, bool] = field(default_factory=lambda: {"enabled": True})


@dataclass
class BingAPIConfig:
    """Bing API 配置"""

    rate_limit: int = 10
    max_retries: int = 3
    timeout: int = 15
    suggestions_per_query: int = 3
    suggestions_per_seed: int = 3
    max_expand: int = 5


@dataclass
class QueryEngineConfig:
    """查询引擎配置"""

    enabled: bool = False
    cache_ttl: int = 3600
    sources: QuerySourcesConfig = field(default_factory=QuerySourcesConfig)
    bing_api: BingAPIConfig = field(default_factory=BingAPIConfig)


@dataclass
class TaskTypesConfig:
    """任务类型配置"""

    url_reward: bool = True
    quiz: bool = False
    poll: bool = False


@dataclass
class TaskSystemConfig:
    """任务系统配置"""

    enabled: bool = True
    min_delay: int = 2
    max_delay: int = 5
    skip_completed: bool = True
    debug_mode: bool = False
    task_types: TaskTypesConfig = field(default_factory=TaskTypesConfig)


@dataclass
class BingThemeConfig:
    """Bing 主题配置"""

    enabled: bool = False
    theme: str = "dark"  # dark, light
    force_theme: bool = True
    persistence_enabled: bool = True
    theme_state_file: str = "logs/theme_state.json"


@dataclass
class MonitoringConfig:
    """监控配置"""

    enabled: bool = True
    check_interval: int = 5
    check_points_before_task: bool = True
    alert_on_no_increase: bool = True
    max_no_increase_count: int = 3
    real_time_display: bool = True


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    enabled: bool = True
    interval: int = 30
    save_reports: bool = True


@dataclass
class MonitoringWithHealth(MonitoringConfig):
    """监控配置（含健康检查）"""

    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)


@dataclass
class TelegramConfig:
    """Telegram 通知配置"""

    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class ServerChanConfig:
    """Server酱通知配置"""

    enabled: bool = False
    key: str = ""


@dataclass
class WhatsAppConfig:
    """WhatsApp 通知配置"""

    enabled: bool = False
    phone: str = ""
    apikey: str = ""


@dataclass
class NotificationConfig:
    """通知配置"""

    enabled: bool = False
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    serverchan: ServerChanConfig = field(default_factory=ServerChanConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)


@dataclass
class SchedulerConfig:
    """调度器配置"""

    enabled: bool = False
    mode: str = "random"  # random, fixed
    random_start_hour: int = 8
    random_end_hour: int = 22
    fixed_hour: int = 10
    fixed_minute: int = 0


@dataclass
class ErrorHandlingConfig:
    """错误处理配置"""

    max_retries: int = 3
    retry_delay: int = 5
    exponential_backoff: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""

    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    file: str = "logs/automator.log"
    console: bool = True


@dataclass
class AppConfig:
    """
    应用程序配置（主配置类）

    聚合所有子配置，提供统一的类型安全访问接口。
    """

    # 主配置节
    search: SearchConfig = field(default_factory=SearchConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    account: AccountConfig = field(default_factory=AccountConfig)
    login: LoginConfig = field(default_factory=LoginConfig)
    query_engine: QueryEngineConfig = field(default_factory=QueryEngineConfig)
    task_system: TaskSystemConfig = field(default_factory=TaskSystemConfig)
    bing_theme: BingThemeConfig = field(default_factory=BingThemeConfig)
    monitoring: MonitoringWithHealth = field(default_factory=MonitoringWithHealth)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    error_handling: ErrorHandlingConfig = field(default_factory=ErrorHandlingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "AppConfig":
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            AppConfig 实例
        """

        def get_nested(obj: Any, key: str, default: Any = None) -> Any:
            """获取嵌套值"""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default

        return cls(
            search=SearchConfig(
                desktop_count=get_nested(config_dict, "desktop_count", 30),
                mobile_count=get_nested(config_dict, "mobile_count", 20),
                wait_interval_min=get_nested(config_dict.get("wait_interval"), "min", 5),
                wait_interval_max=get_nested(config_dict.get("wait_interval"), "max", 15),
                search_terms_file=get_nested(
                    config_dict, "search_terms_file", "tools/search_terms.txt"
                ),
            ),
            browser=BrowserConfig(
                headless=get_nested(config_dict, "headless", False),
                prevent_focus=get_nested(config_dict, "prevent_focus", "basic"),
                slow_mo=get_nested(config_dict, "slow_mo", 100),
                timeout=get_nested(config_dict, "timeout", 30000),
                type=get_nested(config_dict, "type", "chromium"),
            ),
            account=AccountConfig(
                storage_state_path=get_nested(
                    config_dict, "storage_state_path", "storage_state.json"
                ),
                login_url=get_nested(config_dict, "login_url", "https://rewards.microsoft.com/"),
                email=get_nested(config_dict, "email", ""),
                password=get_nested(config_dict, "password", ""),
                totp_secret=get_nested(config_dict, "totp_secret", ""),
            ),
            login=LoginConfig(
                state_machine_enabled=get_nested(config_dict, "state_machine_enabled", True),
                max_transitions=get_nested(config_dict, "max_transitions", 20),
                timeout_seconds=get_nested(config_dict, "timeout_seconds", 300),
                stay_signed_in=get_nested(config_dict, "stay_signed_in", True),
                manual_intervention_timeout=get_nested(
                    config_dict, "manual_intervention_timeout", 120
                ),
                auto_login=AutoLoginConfig(
                    enabled=get_nested(config_dict.get("auto_login", {}), "enabled", False),
                    email=get_nested(config_dict.get("auto_login", {}), "email", ""),
                    password=get_nested(config_dict.get("auto_login", {}), "password", ""),
                    totp_secret=get_nested(config_dict.get("auto_login", {}), "totp_secret", ""),
                ),
            ),
            query_engine=QueryEngineConfig(
                enabled=get_nested(config_dict, "enabled", False),
                cache_ttl=get_nested(config_dict, "cache_ttl", 3600),
            ),
            task_system=TaskSystemConfig(
                enabled=get_nested(config_dict, "enabled", True),
                min_delay=get_nested(config_dict, "min_delay", 2),
                max_delay=get_nested(config_dict, "max_delay", 5),
                skip_completed=get_nested(config_dict, "skip_completed", True),
                debug_mode=get_nested(config_dict, "debug_mode", False),
            ),
            bing_theme=BingThemeConfig(
                enabled=get_nested(config_dict, "enabled", False),
                theme=get_nested(config_dict, "theme", "dark"),
                force_theme=get_nested(config_dict, "force_theme", True),
                persistence_enabled=get_nested(config_dict, "persistence_enabled", True),
            ),
            monitoring=MonitoringWithHealth(
                enabled=get_nested(config_dict, "enabled", True),
                check_interval=get_nested(config_dict, "check_interval", 5),
                check_points_before_task=get_nested(config_dict, "check_points_before_task", True),
                alert_on_no_increase=get_nested(config_dict, "alert_on_no_increase", True),
                max_no_increase_count=get_nested(config_dict, "max_no_increase_count", 3),
                real_time_display=get_nested(config_dict, "real_time_display", True),
            ),
            notification=NotificationConfig(
                enabled=get_nested(config_dict, "enabled", False),
            ),
            scheduler=SchedulerConfig(
                enabled=get_nested(config_dict, "enabled", False),
                mode=get_nested(config_dict, "mode", "random"),
                random_start_hour=get_nested(config_dict, "random_start_hour", 8),
                random_end_hour=get_nested(config_dict, "random_end_hour", 22),
            ),
            error_handling=ErrorHandlingConfig(
                max_retries=get_nested(config_dict, "max_retries", 3),
                retry_delay=get_nested(config_dict, "retry_delay", 5),
                exponential_backoff=get_nested(config_dict, "exponential_backoff", True),
            ),
            logging=LoggingConfig(
                level=get_nested(config_dict, "level", "INFO"),
                file=get_nested(config_dict, "file", "logs/automator.log"),
                console=get_nested(config_dict, "console", True),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, AppConfig):
                result[key] = value.to_dict()
            elif hasattr(value, "__dataclass_fields__"):
                # 处理嵌套 dataclass
                result[key] = {f: getattr(value, f) for f in value.__dataclass_fields__}
            else:
                result[key] = value
        return result
