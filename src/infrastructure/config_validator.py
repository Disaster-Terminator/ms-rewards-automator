"""
配置验证器模块
提供启动时配置验证、错误检测和修复建议
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""

    pass


class ConfigValidator:
    """配置验证器类"""

    def __init__(self, config_manager=None):
        """
        初始化配置验证器

        Args:
            config_manager: ConfigManager实例
        """
        self.config_manager = config_manager
        self.errors = []
        self.warnings = []
        self.suggestions = []

        # 配置规则定义
        self.validation_rules = {
            "search.desktop_count": {
                "type": int,
                "min": 1,
                "max": 50,
                "default": 30,
                "description": "桌面搜索次数",
            },
            "search.mobile_count": {
                "type": int,
                "min": 1,
                "max": 50,  # Increased from 30 to allow more flexibility
                "default": 20,
                "description": "移动搜索次数",
            },
            "search.wait_interval": {
                "type": (int, float, dict),
                "min": 1,
                "max": 30,
                "default": 5,
                "description": "搜索等待间隔（秒）或 {min, max} 字典",
            },
            "search.wait_interval.min": {
                "type": (int, float),
                "min": 0.1,
                "max": 60,
                "default": 2,
                "description": "最小等待时间（已废弃）",
            },
            "search.wait_interval.max": {
                "type": (int, float),
                "min": 0.2,
                "max": 120,
                "default": 5,
                "description": "最大等待时间（已废弃）",
            },
            "browser.headless": {"type": bool, "default": True, "description": "无头模式"},
            "browser.prevent_focus": {
                "type": (str, bool),
                "allowed_values": ["enhanced", "basic", False, "false"],
                "default": "enhanced",
                "description": "防焦点模式",
            },
            "browser.slow_mo": {
                "type": int,
                "min": 0,
                "max": 2000,
                "default": 50,
                "description": "操作延迟",
            },
            "browser.timeout": {
                "type": int,
                "min": 5000,
                "max": 120000,
                "default": 30000,
                "description": "页面超时",
            },
            "account.storage_state_path": {
                "type": str,
                "default": "storage_state.json",
                "description": "会话状态文件路径",
            },
            "monitoring.enabled": {"type": bool, "default": True, "description": "状态监控"},
            "notification.enabled": {"type": bool, "default": False, "description": "通知功能"},
            "logging.level": {
                "type": str,
                "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "default": "INFO",
                "description": "日志级别",
            },
            "bing_theme.enabled": {
                "type": bool,
                "default": True,
                "description": "是否启用主题管理",
            },
            "bing_theme.theme": {
                "type": str,
                "allowed_values": ["dark", "light"],
                "default": "dark",
                "description": "首选主题",
            },
            "bing_theme.force_theme": {
                "type": bool,
                "default": True,
                "description": "是否强制应用主题",
            },
            "bing_theme.persistence_enabled": {
                "type": bool,
                "default": True,
                "description": "是否启用会话间主题保持",
            },
            "bing_theme.theme_state_file": {
                "type": str,
                "default": "logs/theme_state.json",
                "description": "主题状态文件路径",
            },
        }

        logger.info("配置验证器初始化完成")

    def validate_config(self, config_data: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
        """
        验证配置数据

        Args:
            config_data: 配置数据字典

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        self.errors.clear()
        self.warnings.clear()
        self.suggestions.clear()

        logger.info("开始配置验证...")

        # 1. 验证必需的配置项
        self._validate_required_fields(config_data)

        # 2. 验证数据类型和范围
        self._validate_field_types_and_ranges(config_data)

        # 3. 验证逻辑一致性
        self._validate_logical_consistency(config_data)

        # 4. 验证文件路径
        self._validate_file_paths(config_data)

        # 5. 验证通知配置
        self._validate_notification_config(config_data)

        # 6. 生成优化建议
        self._generate_optimization_suggestions(config_data)

        is_valid = len(self.errors) == 0

        if is_valid:
            logger.info("✓ 配置验证通过")
        else:
            logger.warning(f"配置验证失败: {len(self.errors)} 个错误, {len(self.warnings)} 个警告")

        return is_valid, self.errors.copy(), self.warnings.copy()

    def _validate_required_fields(self, config_data: dict[str, Any]):
        """验证必需字段"""
        required_sections = ["search", "browser", "account"]

        for section in required_sections:
            if section not in config_data:
                self.errors.append(f"缺少必需的配置节: '{section}'")
                continue

            if not isinstance(config_data[section], dict):
                self.errors.append(f"配置节 '{section}' 必须是字典类型")

    def _validate_field_types_and_ranges(self, config_data: dict[str, Any]):
        """验证字段类型和范围"""
        for field_path, rules in self.validation_rules.items():
            value = self._get_nested_value(config_data, field_path)

            if value is None:
                # 使用默认值
                if "default" in rules:
                    self.warnings.append(
                        f"字段 '{field_path}' 未设置，将使用默认值: {rules['default']}"
                    )
                continue

            # 类型检查
            expected_type = rules.get("type")
            if expected_type:
                # 处理元组类型（多个允许的类型）
                if isinstance(expected_type, tuple):
                    if not any(isinstance(value, t) for t in expected_type):
                        type_names = " 或 ".join(t.__name__ for t in expected_type)
                        self.errors.append(
                            f"字段 '{field_path}' 类型错误: 期望 {type_names}, 实际 {type(value).__name__}"
                        )
                        continue
                else:
                    # 单一类型检查
                    if not isinstance(value, expected_type):
                        self.errors.append(
                            f"字段 '{field_path}' 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
                        )
                        continue

            # 范围检查
            if isinstance(value, (int, float)):
                min_val = rules.get("min")
                max_val = rules.get("max")

                if min_val is not None and value < min_val:
                    self.errors.append(f"字段 '{field_path}' 值过小: {value} < {min_val}")

                if max_val is not None and value > max_val:
                    self.errors.append(f"字段 '{field_path}' 值过大: {value} > {max_val}")

            # 允许值检查
            allowed_values = rules.get("allowed_values")
            if allowed_values and value not in allowed_values:
                self.errors.append(
                    f"字段 '{field_path}' 值无效: {value}, 允许的值: {allowed_values}"
                )

    def _validate_logical_consistency(self, config_data: dict[str, Any]):
        """验证逻辑一致性"""
        # 检查等待时间逻辑
        wait_min = self._get_nested_value(config_data, "search.wait_interval.min")
        wait_max = self._get_nested_value(config_data, "search.wait_interval.max")

        if wait_min and wait_max and wait_min >= wait_max:
            self.errors.append(f"等待时间配置错误: min ({wait_min}) 必须小于 max ({wait_max})")

        # 检查搜索次数合理性
        desktop_count = self._get_nested_value(config_data, "search.desktop_count")
        mobile_count = self._get_nested_value(config_data, "search.mobile_count")

        if desktop_count and desktop_count > 35:
            self.warnings.append(
                f"桌面搜索次数 ({desktop_count}) 超过推荐值 (30), 可能增加被检测风险"
            )

        if mobile_count and isinstance(mobile_count, (int, float)) and mobile_count > 25:
            self.warnings.append(
                f"移动搜索次数 ({mobile_count}) 超过推荐值 (20), 可能增加被检测风险"
            )

        # 检查防焦点配置逻辑
        headless = self._get_nested_value(config_data, "browser.headless")
        prevent_focus = self._get_nested_value(config_data, "browser.prevent_focus")

        if headless and prevent_focus:
            self.warnings.append("无头模式下防焦点设置无效，建议在有头模式下使用防焦点功能")

    def _validate_file_paths(self, config_data: dict[str, Any]):
        """验证文件路径"""
        # 检查搜索词文件
        search_terms_file = self._get_nested_value(config_data, "search.search_terms_file")
        if search_terms_file:
            if not os.path.exists(search_terms_file):
                self.warnings.append(f"搜索词文件不存在: {search_terms_file}")

        # 检查日志目录
        log_file = self._get_nested_value(config_data, "logging.file")
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                    self.suggestions.append(f"已自动创建日志目录: {log_dir}")
                except Exception as e:
                    self.warnings.append(f"无法创建日志目录 {log_dir}: {e}")

    def _validate_notification_config(self, config_data: dict[str, Any]):
        """验证通知配置"""
        notification_enabled = self._get_nested_value(config_data, "notification.enabled")

        if not notification_enabled:
            return

        # 检查通知服务配置
        notification_config = config_data.get("notification", {})

        services = ["telegram", "serverchan", "whatsapp"]
        enabled_services = []

        for service in services:
            service_config = notification_config.get(service, {})
            if service_config.get("enabled", False):
                enabled_services.append(service)

                # 验证必需字段
                if service == "telegram":
                    if not service_config.get("bot_token"):
                        self.errors.append("Telegram通知已启用但缺少bot_token")
                    if not service_config.get("chat_id"):
                        self.errors.append("Telegram通知已启用但缺少chat_id")

                elif service == "serverchan":
                    if not service_config.get("key"):
                        self.errors.append("Server酱通知已启用但缺少key")

                elif service == "whatsapp":
                    if not service_config.get("phone"):
                        self.errors.append("WhatsApp通知已启用但缺少phone")
                    if not service_config.get("apikey"):
                        self.errors.append("WhatsApp通知已启用但缺少apikey")

        if not enabled_services:
            self.warnings.append("通知功能已启用但没有配置任何通知服务")

    def _generate_optimization_suggestions(self, config_data: dict[str, Any]):
        """生成优化建议"""
        # 性能优化建议
        slow_mo = self._get_nested_value(config_data, "browser.slow_mo")
        if slow_mo and slow_mo > 200:
            self.suggestions.append(f"当前操作延迟 ({slow_mo}ms) 较高，可以适当降低以提高执行速度")

        # 安全性建议
        wait_max = self._get_nested_value(config_data, "search.wait_interval.max")
        if wait_max and wait_max < 5:
            self.suggestions.append("建议增加最大等待时间 (>= 5秒) 以降低被检测风险")

        # 监控建议
        monitoring_enabled = self._get_nested_value(config_data, "monitoring.enabled")
        if not monitoring_enabled:
            self.suggestions.append("建议启用状态监控以便及时发现问题")

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """获取嵌套字典值"""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def get_validation_report(self) -> str:
        """获取验证报告"""
        report = []
        report.append("=" * 60)
        report.append("配置验证报告")
        report.append("=" * 60)

        if self.errors:
            report.append(f"\n❌ 错误 ({len(self.errors)} 个):")
            for i, error in enumerate(self.errors, 1):
                report.append(f"  {i}. {error}")

        if self.warnings:
            report.append(f"\n⚠️  警告 ({len(self.warnings)} 个):")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"  {i}. {warning}")

        if self.suggestions:
            report.append(f"\n💡 建议 ({len(self.suggestions)} 个):")
            for i, suggestion in enumerate(self.suggestions, 1):
                report.append(f"  {i}. {suggestion}")

        if not self.errors and not self.warnings:
            report.append("\n✅ 配置验证通过，没有发现问题")

        report.append("=" * 60)
        return "\n".join(report)

    def fix_common_issues(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """自动修复常见配置问题"""
        fixed_config = config_data.copy()
        fixes_applied = []

        # 修复等待时间逻辑错误
        wait_min = self._get_nested_value(fixed_config, "search.wait_interval.min")
        wait_max = self._get_nested_value(fixed_config, "search.wait_interval.max")

        if wait_min and wait_max and wait_min >= wait_max:
            if "search" not in fixed_config:
                fixed_config["search"] = {}
            if "wait_interval" not in fixed_config["search"]:
                fixed_config["search"]["wait_interval"] = {}

            fixed_config["search"]["wait_interval"]["min"] = 2
            fixed_config["search"]["wait_interval"]["max"] = 5
            fixes_applied.append("修复等待时间配置: min=2, max=5")

        # 修复防焦点配置
        prevent_focus = self._get_nested_value(fixed_config, "browser.prevent_focus")
        if prevent_focus not in ["enhanced", "basic", False, "false"]:
            if "browser" not in fixed_config:
                fixed_config["browser"] = {}
            fixed_config["browser"]["prevent_focus"] = "enhanced"
            fixes_applied.append("修复防焦点配置为 'enhanced'")

        # 添加缺失的默认值
        for field_path, rules in self.validation_rules.items():
            if self._get_nested_value(fixed_config, field_path) is None and "default" in rules:
                self._set_nested_value(fixed_config, field_path, rules["default"])
                fixes_applied.append(f"添加默认值: {field_path} = {rules['default']}")

        if fixes_applied:
            logger.info(f"应用了 {len(fixes_applied)} 个自动修复:")
            for fix in fixes_applied:
                logger.info(f"  - {fix}")

        return fixed_config

    def _set_nested_value(self, data: dict[str, Any], path: str, value: Any):
        """设置嵌套字典值"""
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def validate_config_file(config_path: str) -> tuple[bool, str]:
        """
        验证配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            (是否有效, 验证报告)
        """
        try:
            from .config_manager import ConfigManager

            # 加载配置
            config_manager = ConfigManager(config_path)

            # 创建验证器
            validator = ConfigValidator(config_manager)

            # 执行验证
            is_valid, errors, warnings = validator.validate_config(config_manager.config)

            # 生成报告
            report = validator.get_validation_report()

            return is_valid, report

        except Exception as e:
            error_report = f"配置文件验证失败: {e}"
            return False, error_report
