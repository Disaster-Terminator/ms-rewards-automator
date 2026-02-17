"""
配置服务
管理应用配置
"""

import copy
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigService:
    """配置服务类"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置服务

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"配置已加载: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "search": {
                "desktop_count": 30,
                "mobile_count": 20,
                "wait_interval": 5,
            },
            "browser": {
                "headless": False,
                "type": "chromium",
                "force_dark_mode": False,
            },
            "account": {
                "storage_state_path": "storage_state.json",
                "login_url": "https://rewards.microsoft.com/",
            },
            "login": {
                "auto_login": {
                    "enabled": False,
                    "email": "",
                    "password": "",
                    "totp_secret": "",
                }
            },
            "task_system": {
                "enabled": False,
                "debug_mode": False,
            },
            "notification": {
                "enabled": False,
                "telegram": {
                    "bot_token": "",
                    "chat_id": "",
                }
            },
            "scheduler": {
                "enabled": False,
                "mode": "random",
                "random_start_hour": 8,
                "random_end_hour": 22,
            },
            "logging": {
                "level": "INFO",
            },
            "bing_theme": {
                "enabled": False,
                "force_theme": False,
            },
            "monitoring": {
                "health_check": {
                    "enabled": False,
                    "interval": 30,
                }
            },
        }

    def get_config(self) -> dict[str, Any]:
        """获取完整配置"""
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键 (支持点号分隔的嵌套键)
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键 (支持点号分隔的嵌套键)
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def update_config(self, updates: dict[str, Any]):
        """
        更新配置

        Args:
            updates: 更新内容
        """
        def deep_update(base: dict, updates: dict):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value

        deep_update(self._config, updates)
        self._save_config()

    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def get_summary(self) -> dict[str, Any]:
        """获取配置摘要"""
        return {
            "search_counts": {
                "desktop": self.get("search.desktop_count", 30),
                "mobile": self.get("search.mobile_count", 20),
            },
            "browser_type": self.get("browser.type", "chromium"),
            "headless": self.get("browser.headless", False),
            "auto_login": self.get("login.auto_login.enabled", False),
            "task_system_enabled": self.get("task_system.enabled", False),
            "notification_enabled": self.get("notification.enabled", False),
            "scheduler_enabled": self.get("scheduler.enabled", False),
        }

    def validate(self) -> tuple:
        """
        验证配置

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        desktop_count = self.get("search.desktop_count", 30)
        mobile_count = self.get("search.mobile_count", 20)

        if desktop_count < 0 or desktop_count > 100:
            errors.append(f"桌面搜索次数无效: {desktop_count}")
        if mobile_count < 0 or mobile_count > 100:
            errors.append(f"移动搜索次数无效: {mobile_count}")

        browser_type = self.get("browser.type", "chromium")
        if browser_type not in ["chromium", "chrome", "edge"]:
            errors.append(f"不支持的浏览器类型: {browser_type}")

        if self.get("login.auto_login.enabled", False):
            email = self.get("login.auto_login.email", "")
            if not email:
                errors.append("自动登录已启用但未配置邮箱")

        return len(errors) == 0, errors, warnings
