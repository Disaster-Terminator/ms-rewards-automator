"""
配置管理器模块
负责加载、验证和提供配置参数
"""

import logging
import os
from typing import Any

import yaml

from constants import REWARDS_URLS

logger = logging.getLogger(__name__)


EXECUTION_MODE_PRESETS = {
    "fast": {
        "search": {"wait_interval": {"min": 2, "max": 5}},
        "browser": {"slow_mo": 50},
    },
    "normal": {
        "search": {"wait_interval": {"min": 5, "max": 15}},
        "browser": {"slow_mo": 100},
    },
    "slow": {
        "search": {"wait_interval": {"min": 15, "max": 30}},
        "browser": {"slow_mo": 200},
    },
}


DEFAULT_CONFIG = {
    "execution": {
        "mode": "normal",
    },
    "search": {
        "desktop_count": 20,
        "mobile_count": 0,
        "wait_interval": {"min": 5, "max": 15},
        "search_terms_file": "tools/search_terms.txt",
    },
    "browser": {
        "headless": False,
        "prevent_focus": "basic",
        "slow_mo": 100,
        "timeout": 30000,
        "type": "chromium",
    },
    "account": {
        "storage_state_path": "storage_state.json",
        "login_url": REWARDS_URLS["rewards_home"],
    },
    "login": {
        "state_machine_enabled": True,
        "max_transitions": 20,
        "timeout_seconds": 300,
        "stay_signed_in": True,
        "manual_intervention_timeout": 120,
        "auto_login": {"enabled": False, "email": "", "password": "", "totp_secret": ""},
    },
    "query_engine": {
        "enabled": False,
        "cache_ttl": 3600,
        "sources": {
            "local_file": {"enabled": True},
            "bing_suggestions": {"enabled": True},
            "duckduckgo": {"enabled": True},
            "wikipedia": {"enabled": True},
        },
        "bing_api": {
            "rate_limit": 10,
            "max_retries": 3,
            "timeout": 15,
            "suggestions_per_query": 3,
            "suggestions_per_seed": 3,
            "max_expand": 5,
        },
    },
    "task_system": {
        "enabled": False,
        "min_delay": 2,
        "max_delay": 5,
        "skip_completed": True,
        "debug_mode": False,
        "task_types": {"url_reward": True, "quiz": False, "poll": False},
        "task_parser": {
            "skip_hrefs": [
                "/earn",
                "/dashboard",
                "/about",
                "/refer",
                "/",
                "/orderhistory",
                "/faq",
                "rewards.bing.com/referandearn",
                "rewards.bing.com/redeem",
                "support.microsoft.com",
                "x.com",
                "xbox.com",
                "microsoft.com/about",
                "news.microsoft.com",
                "go.microsoft.com",
                "choice.microsoft.com",
                "microsoft-edge://",
            ],
            "skip_text_patterns": ["抽奖", "sweepstakes"],
            "completed_text_patterns": ["已完成", "completed"],
            "points_selector": ".text-caption1Stronger",
            "completed_circle_class": "bg-statusSuccessBg3",
            "incomplete_circle_class": "border-neutralStroke1",
            "login_selectors": [
                'input[name="loginfmt"]',
                'input[type="email"]',
                "#i0116",
            ],
            "earn_link_selector": 'a[href="/earn"], a[href^="/earn?"], a[href*="rewards.bing.com/earn"]',
        },
    },
    "bing_theme": {
        "enabled": False,
        "theme": "dark",
        "force_theme": True,
        "persistence_enabled": True,
        "theme_state_file": "logs/theme_state.json",
    },
    "monitoring": {
        "enabled": True,
        "check_interval": 5,
        "check_points_before_task": True,
        "alert_on_no_increase": True,
        "max_no_increase_count": 3,
        "real_time_display": True,
        "health_check": {"enabled": True, "interval": 30, "save_reports": True},
    },
    "notification": {
        "enabled": False,
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
        "serverchan": {"enabled": False, "key": ""},
        "whatsapp": {"enabled": False, "phone": "", "apikey": ""},
    },
    "scheduler": {
        "enabled": True,
        "mode": "scheduled",
        "scheduled_hour": 17,
        "max_offset_minutes": 45,
        "random_start_hour": 8,
        "random_end_hour": 22,
        "fixed_hour": 10,
        "fixed_minute": 0,
    },
    "anti_detection": {
        "use_stealth": True,
        "random_viewport": True,
        "human_behavior_level": "medium",
        "scroll_behavior": {
            "enabled": True,
            "min_scrolls": 2,
            "max_scrolls": 5,
            "scroll_delay_min": 500,
            "scroll_delay_max": 2000,
        },
        "mouse_movement": {
            "enabled": True,
            "micro_movement_probability": 0.3,
        },
        "typing": {
            "use_gaussian_delay": True,
            "avg_delay_ms": 120,
            "std_delay_ms": 30,
            "pause_probability": 0.1,
        },
    },
    "error_handling": {"max_retries": 3, "retry_delay": 5, "exponential_backoff": True},
    "logging": {"level": "INFO", "file": "logs/automator.log", "console": True},
}

# 开发模式覆盖配置 - 用于快速迭代调试
DEV_MODE_OVERRIDES = {
    "search": {
        "desktop_count": 2,
        "mobile_count": 0,
        "wait_interval": {
            "min": 0.5,
            "max": 1.5,
        },
    },
    "browser": {"slow_mo": 0, "headless": False},
    "anti_detection": {
        "use_stealth": False,
        "random_viewport": False,
        "scroll_behavior": {"enabled": False},
    },
    "monitoring": {
        "enabled": True,
    },
    "bing_theme": {
        "enabled": True,
        "persistence_enabled": True,
    },
    "task_system": {
        "enabled": True,
        "debug_mode": True,
        "max_tasks": 2,
    },
    "scheduler": {
        "enabled": False,
    },
    "logging": {"level": "DEBUG"},
}

# 用户模式覆盖配置 - 用于鲁棒性测试，模拟真实使用环境
USER_MODE_OVERRIDES = {
    "search": {
        "desktop_count": 3,
        "mobile_count": 0,
        "wait_interval": {
            "min": 3,
            "max": 8,
        },
    },
    "browser": {"slow_mo": 50, "headless": False},
    "anti_detection": {
        "use_stealth": True,
        "random_viewport": True,
        "scroll_behavior": {
            "enabled": True,
            "min_scrolls": 2,
            "max_scrolls": 4,
        },
    },
    "monitoring": {
        "enabled": True,
    },
    "bing_theme": {
        "enabled": True,
        "persistence_enabled": True,
    },
    "task_system": {
        "enabled": True,
        "debug_mode": False,
    },
    "scheduler": {
        "enabled": False,
    },
    "logging": {"level": "INFO"},
}


class ConfigManager:
    """配置管理器类"""

    def __init__(
        self, config_path: str = "config.yaml", dev_mode: bool = False, user_mode: bool = False
    ):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
            dev_mode: 是否启用开发模式（快速迭代调试）
            user_mode: 是否启用用户模式（鲁棒性测试，模拟真实环境）
        """
        self.config_path = config_path
        self.dev_mode = dev_mode
        self.user_mode = user_mode
        self.config: dict[str, Any] = {}  # 使用 dict 而非 ConfigDict，避免 TypedDict 初始化问题
        self.config_data: dict[str, Any] = {}
        self._load_config()

        self._apply_execution_mode()

        if self.dev_mode:
            self._apply_dev_mode()
            logger.info("🚀 开发模式已启用")
        elif self.user_mode:
            self._apply_user_mode()
            logger.info("🎯 用户模式已启用")

    def _apply_execution_mode(self) -> None:
        """应用执行模式预设配置"""
        execution = self.config.get("execution")
        if isinstance(execution, dict):
            mode = execution.get("mode", "normal")
        else:
            if execution is not None:
                logger.warning(
                    "配置项 execution 应为字典类型，实际为 %s，已忽略并使用 normal",
                    type(execution).__name__,
                )
            mode = "normal"
        if mode not in EXECUTION_MODE_PRESETS:
            logger.warning(f"未知的执行模式: {mode}，使用 normal")
            mode = "normal"

        if mode != "normal":
            preset = EXECUTION_MODE_PRESETS[mode]
            self.config = self._merge_configs(self.config, preset)
            self.config_data = self.config
            logger.info(f"⚡ 执行模式: {mode}")

    def _apply_dev_mode(self) -> None:
        """应用开发模式覆盖配置"""
        self.config = self._merge_configs(self.config, DEV_MODE_OVERRIDES)
        self.config_data = self.config
        logger.debug("开发模式配置已应用")

    def _apply_user_mode(self) -> None:
        """应用用户模式覆盖配置"""
        self.config = self._merge_configs(self.config, USER_MODE_OVERRIDES)
        self.config_data = self.config
        logger.debug("用户模式配置已应用")

    def _load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)

            if loaded_config is None:
                logger.warning("配置文件为空，使用默认配置")
                self.config = DEFAULT_CONFIG.copy()
                return

            # 合并加载的配置和默认配置
            self.config = self._merge_configs(DEFAULT_CONFIG, loaded_config)

            # 向后兼容：处理 wait_interval 从 int 到 dict 的变化
            wait_interval = self.config.get("search", {}).get("wait_interval")
            if isinstance(wait_interval, (int, float)):
                logger.warning(
                    f"wait_interval 使用旧格式 (int: {wait_interval})，"
                    "建议更新为 {min: X, max: Y} 格式"
                )
                self.config["search"]["wait_interval"] = {
                    "min": wait_interval,
                    "max": wait_interval + 10,
                }

            # 向后兼容：处理旧的 account.email/password/totp_secret
            if "account" in self.config:
                if "email" in self.config["account"] and "login" in self.config:
                    if "auto_login" not in self.config["login"]:
                        self.config["login"]["auto_login"] = {}
                    self.config["login"]["auto_login"]["email"] = self.config["account"].get(
                        "email", ""
                    )
                    self.config["login"]["auto_login"]["password"] = self.config["account"].get(
                        "password", ""
                    )
                    self.config["login"]["auto_login"]["totp_secret"] = self.config["account"].get(
                        "totp_secret", ""
                    )
                    # 如果配置了凭据，默认启用自动登录
                    if self.config["login"]["auto_login"]["email"]:
                        self.config["login"]["auto_login"]["enabled"] = True
                        logger.debug("检测到旧配置格式，已迁移到 login.auto_login")

            # 保持向后兼容
            self.config_data = self.config

            logger.info(f"配置文件加载成功: {self.config_path}")

        except yaml.YAMLError as e:
            logger.error(f"配置文件解析失败: {e}")
            logger.warning("使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"加载配置文件时出错: {e}")
            logger.warning("使用默认配置")
            self.config = DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: dict, loaded: dict) -> dict:
        """
        递归合并配置字典

        Args:
            default: 默认配置
            loaded: 加载的配置

        Returns:
            合并后的配置
        """
        import copy

        result = copy.deepcopy(default)

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def load_config(self) -> dict[str, Any]:
        """
        加载配置文件，返回配置字典

        Returns:
            配置字典
        """
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持嵌套键（如 'search.desktop_count'）

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_with_env(self, key: str, env_var: str, default: Any = None) -> Any:
        """
        获取配置项，优先从环境变量读取

        Args:
            key: 配置键，支持点号分隔的嵌套键
            env_var: 环境变量名
            default: 默认值

        Returns:
            配置值（环境变量优先）
        """
        return os.environ.get(env_var) or self.get(key, default)

    def validate_config(self, auto_fix: bool = False) -> bool:
        """
        验证配置文件的完整性和有效性

        Args:
            auto_fix: 是否自动修复常见问题

        Returns:
            配置是否有效
        """
        try:
            from .config_validator import ConfigValidator

            validator = ConfigValidator(self)
            is_valid, errors, warnings = validator.validate_config(self.config)

            # 显示验证报告
            if errors or warnings:
                report = validator.get_validation_report()
                print(report)

            # 自动修复（如果启用）
            if auto_fix and (errors or warnings):
                logger.info("尝试自动修复配置问题...")
                fixed_config = validator.fix_common_issues(self.config)

                if fixed_config != self.config:
                    self.config = fixed_config
                    logger.info("配置已自动修复")

                    # 重新验证
                    is_valid, _, _ = validator.validate_config(self.config)

            return is_valid

        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False

    def validate_browser_config(self) -> tuple[bool, list[str]]:
        """
        验证浏览器相关配置

        Returns:
            (是否有效, 警告信息列表)
        """
        warnings = []
        is_valid = True

        headless = self.get("browser.headless")
        silent_mode = self.get("browser.silent_mode")
        prevent_focus = self.get("browser.prevent_focus")

        # 逻辑一致性检查
        if headless and (silent_mode or prevent_focus):
            warnings.append("无头模式下，silent_mode和prevent_focus配置无效")

        if not headless and not silent_mode and not prevent_focus:
            warnings.append("有头模式下建议启用silent_mode或prevent_focus以避免窗口干扰")

        if silent_mode and not prevent_focus:
            warnings.append("启用silent_mode时建议同时启用prevent_focus以获得最佳效果")

        return is_valid, warnings

    def get_effective_browser_config(self) -> dict:
        """
        获取有效的浏览器配置（考虑逻辑依赖）

        Returns:
            有效的浏览器配置字典
        """
        config = {
            "headless": self.get("browser.headless", False),
            "prevent_focus": self.get("browser.prevent_focus", "enhanced"),
            "slow_mo": self.get("browser.slow_mo", 100),
            "timeout": self.get("browser.timeout", 30000),
        }

        # 向后兼容：处理旧的配置格式
        silent_mode = self.get("browser.silent_mode")
        old_prevent_focus = self.get("browser.prevent_focus")

        if silent_mode is not None and isinstance(old_prevent_focus, bool):
            # 旧配置格式转换
            if old_prevent_focus:
                config["prevent_focus"] = "enhanced" if silent_mode else "basic"
            else:
                config["prevent_focus"] = False

        # 如果是无头模式，防焦点配置无效但保留设置
        if config["headless"]:
            logger.debug("无头模式下防焦点配置无效")

        return config

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ConfigManager(config_path='{self.config_path}')"
