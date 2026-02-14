"""
配置管理器模块
负责加载、验证和提供配置参数
"""

import os
import logging
from pathlib import Path
from typing import Any, Optional, Dict
import yaml


logger = logging.getLogger(__name__)


# 默认配置（完整的技术参数）
DEFAULT_CONFIG = {
    "search": {
        "desktop_count": 30,
        "mobile_count": 20,
        "wait_interval": 5,  # 简化为单个值
        "search_terms_file": "tools/search_terms.txt"
    },
    "browser": {
        "headless": False,
        "prevent_focus": "basic",
        "slow_mo": 100,
        "timeout": 30000,
        "type": "chromium"
    },
    "account": {
        "storage_state_path": "storage_state.json",
        "login_url": "https://rewards.microsoft.com/"
    },
    "login": {
        "state_machine_enabled": True,
        "max_transitions": 20,
        "timeout_seconds": 300,
        "stay_signed_in": True,
        "manual_intervention_timeout": 120,
        "auto_login": {
            "enabled": False,
            "email": "",
            "password": "",
            "totp_secret": ""
        }
    },
    "query_engine": {
        "enabled": False,
        "cache_ttl": 3600,
        "sources": {
            "local_file": {"enabled": True},
            "bing_suggestions": {"enabled": True}
        },
        "bing_api": {
            "rate_limit": 10,
            "max_retries": 3,
            "timeout": 15,
            "suggestions_per_query": 3,
            "suggestions_per_seed": 3,
            "max_expand": 5
        }
    },
    "task_system": {
        "enabled": True,
        "min_delay": 2,
        "max_delay": 5,
        "skip_completed": True,
        "debug_mode": False,
        "task_types": {
            "url_reward": True,
            "quiz": False,
            "poll": False
        }
    },
    "bing_theme": {
        "enabled": False,
        "theme": "dark",
        "force_theme": True,
        "persistence_enabled": True,
        "theme_state_file": "theme_state.json"
    },
    "monitoring": {
        "enabled": True,
        "check_interval": 5,
        "check_points_before_task": True,
        "alert_on_no_increase": True,
        "max_no_increase_count": 3,
        "real_time_display": True,
        "health_check": {
            "enabled": True,
            "interval": 30,
            "save_reports": True
        }
    },
    "notification": {
        "enabled": False,
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        },
        "serverchan": {
            "enabled": False,
            "key": ""
        },
        "whatsapp": {
            "enabled": False,
            "phone": "",
            "apikey": ""
        }
    },
    "scheduler": {
        "enabled": False,
        "mode": "random",
        "random_start_hour": 8,
        "random_end_hour": 22,
        "fixed_hour": 10,
        "fixed_minute": 0
    },
    "error_handling": {
        "max_retries": 3,
        "retry_delay": 5,
        "exponential_backoff": True
    },
    "logging": {
        "level": "INFO",
        "file": "logs/automator.log",
        "console": True
    }
}

# 开发模式覆盖配置
DEV_MODE_OVERRIDES = {
    "search": {
        # 开发模式：极简搜索数量 + 更短的等待时间
        "desktop_count": 2,
        "mobile_count": 2,
        # 使用区间形式，方便 AntiBanModule 读取 min/max
        "wait_interval": {
            "min": 0.5,
            "max": 1.5,
        },
    },
    "browser": {
        # 开发模式尽量减少慢动作，加快调试速度
        "slow_mo": 0,
        "headless": False
    },
    # 开发模式弱化反检测，避免额外耗时
    "anti_detection": {
        "use_stealth": False,
        "random_viewport": False,
        "scroll_behavior": {
            "enabled": False
        }
    },
    # 开发模式下启用积分监控，便于测试完整流程
    "monitoring": {
        "enabled": True,
    },
    # 开发模式下禁用主题管理，避免自动导航干扰任务流程
    "bing_theme": {
        "enabled": False,
        "persistence_enabled": False,
    },
    # 开发模式下保留监控与任务执行，但提高可观测性（由各模块内部根据 dev_mode 决定是否降级行为）
    "task_system": {
        "enabled": True,  # 开发模式下启用任务系统
        "debug_mode": True,
        "max_tasks": 2,  # 开发模式只执行少量任务
    },
    "logging": {
        "level": "DEBUG"
    }
}


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_path: str = "config.yaml", dev_mode: bool = False):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
            dev_mode: 是否启用开发模式
        """
        self.config_path = config_path
        self.dev_mode = dev_mode
        self.config: Dict[str, Any] = {}
        self.config_data: Dict[str, Any] = {}  # 保持向后兼容
        self._load_config()

        # 初始化类型化配置
        self._init_typed_config()

        # 如果启用开发模式，应用覆盖配置
        if self.dev_mode:
            self._apply_dev_mode()
            logger.info("🚀 开发模式已启用")

    def _init_typed_config(self) -> None:
        """初始化类型化配置"""
        try:
            from .app_config import AppConfig
            self.app = AppConfig.from_dict(self.config)
        except Exception as e:
            logger.warning(f"类型化配置初始化失败，使用字典配置: {e}")
            self.app = None
    
    def _apply_dev_mode(self) -> None:
        """应用开发模式覆盖配置"""
        self.config = self._merge_configs(self.config, DEV_MODE_OVERRIDES)
        self.config_data = self.config  # 保持同步
        # 同步更新类型化配置
        if self.app:
            self.app = type(self.app).from_dict(self.config)
        logger.debug("开发模式配置已应用")
    
    def _load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            if loaded_config is None:
                logger.warning("配置文件为空，使用默认配置")
                self.config = DEFAULT_CONFIG.copy()
                return
            
            # 合并加载的配置和默认配置
            self.config = self._merge_configs(DEFAULT_CONFIG, loaded_config)
            
            # 向后兼容：处理 wait_interval 从 dict 到 int 的变化
            if isinstance(self.config.get("search", {}).get("wait_interval"), dict):
                wait_min = self.config["search"]["wait_interval"].get("min", 3)
                wait_max = self.config["search"]["wait_interval"].get("max", 8)
                # 使用中间值
                self.config["search"]["wait_interval"] = (wait_min + wait_max) // 2
                logger.debug(f"wait_interval 已从 dict 转换为 int: {self.config['search']['wait_interval']}")
            
            # 向后兼容：处理旧的 account.email/password/totp_secret
            if "account" in self.config:
                if "email" in self.config["account"] and "login" in self.config:
                    if "auto_login" not in self.config["login"]:
                        self.config["login"]["auto_login"] = {}
                    self.config["login"]["auto_login"]["email"] = self.config["account"].get("email", "")
                    self.config["login"]["auto_login"]["password"] = self.config["account"].get("password", "")
                    self.config["login"]["auto_login"]["totp_secret"] = self.config["account"].get("totp_secret", "")
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
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """
        递归合并配置字典
        
        Args:
            default: 默认配置
            loaded: 加载的配置
            
        Returns:
            合并后的配置
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_config(self) -> Dict[str, Any]:
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
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate_config(self, auto_fix: bool = False) -> bool:
        """
        验证配置文件的完整性和有效性（增强版）
        
        Args:
            auto_fix: 是否自动修复常见问题
            
        Returns:
            配置是否有效
        """
        try:
            # 使用新的配置验证器
            from config_validator import ConfigValidator
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
            
        except ImportError:
            # 降级到原有的验证逻辑
            logger.debug("使用基础配置验证")
            return self._validate_config_basic()
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return self._validate_config_basic()
    
    def _validate_config_basic(self) -> bool:
        """
        基础配置验证（原有逻辑）
        
        Returns:
            配置是否有效
        """
        required_keys = [
            "search.desktop_count",
            "search.mobile_count",
            "search.wait_interval",
            "browser.headless",
            "account.storage_state_path",
            "logging.level"
        ]
        
        for key in required_keys:
            value = self.get(key)
            if value is None:
                logger.error(f"缺少必需的配置项: {key}")
                return False
        
        # 验证数值范围
        desktop_count = self.get("search.desktop_count")
        if not isinstance(desktop_count, int) or desktop_count < 1:
            logger.error(f"search.desktop_count 必须是正整数: {desktop_count}")
            return False
        
        mobile_count = self.get("search.mobile_count")
        if not isinstance(mobile_count, int) or mobile_count < 1:
            logger.error(f"search.mobile_count 必须是正整数: {mobile_count}")
            return False
        
        # 验证 wait_interval（支持单个值和字典两种格式）
        wait_interval = self.get("search.wait_interval")
        if isinstance(wait_interval, dict):
            wait_min = wait_interval.get("min")
            wait_max = wait_interval.get("max")
            if wait_min is None or wait_max is None:
                logger.error("wait_interval 字典必须包含 min 和 max 键")
                return False
            if not isinstance(wait_min, (int, float)) or not isinstance(wait_max, (int, float)):
                logger.error("wait_interval.min 和 wait_interval.max 必须是数字")
                return False
            if wait_min >= wait_max:
                logger.error(f"wait_interval.min ({wait_min}) 必须小于 wait_interval.max ({wait_max})")
                return False
        elif isinstance(wait_interval, (int, float)):
            if wait_interval <= 0:
                logger.error(f"wait_interval 必须为正数: {wait_interval}")
                return False
        else:
            logger.error(f"wait_interval 格式无效，应为数字或包含 min/max 的字典: {wait_interval}")
            return False
        
        # 验证浏览器配置
        headless = self.get("browser.headless")
        if not isinstance(headless, bool):
            logger.error(f"browser.headless 必须是布尔值: {headless}")
            return False
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self.get("logging.level")
        if log_level not in valid_log_levels:
            logger.error(f"无效的日志级别: {log_level}，有效值: {valid_log_levels}")
            return False
        
        logger.info("配置验证通过")
        return True
    
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
            "timeout": self.get("browser.timeout", 30000)
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
