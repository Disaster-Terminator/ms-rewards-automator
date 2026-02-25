"""
ConfigValidator 单元测试
测试配置验证器的各项功能
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config_validator import ConfigValidator


class TestConfigValidator:
    """ConfigValidator 测试类"""

    @pytest.fixture
    def mock_config_manager(self):
        """创建 Mock ConfigManager"""
        mock_manager = Mock()
        mock_manager.config = {
            "search": {
                "desktop_count": 20,
                "mobile_count": 0,
                "wait_interval": {"min": 2, "max": 5},
            },
            "browser": {
                "headless": True,
                "prevent_focus": "enhanced",
                "slow_mo": 50,
                "timeout": 30000,
            },
            "account": {"storage_state_path": "storage_state.json"},
            "monitoring": {"enabled": True},
            "notification": {"enabled": False},
        }
        mock_manager.get_with_env = Mock(return_value=None)
        return mock_manager

    @pytest.fixture
    def validator(self, mock_config_manager):
        """创建 ConfigValidator 实例"""
        return ConfigValidator(mock_config_manager)

    @pytest.fixture
    def valid_config(self):
        """创建有效的配置数据"""
        return {
            "search": {
                "desktop_count": 20,
                "mobile_count": 0,
                "wait_interval": {"min": 2, "max": 5},
            },
            "browser": {
                "headless": True,
                "prevent_focus": "enhanced",
                "slow_mo": 50,
                "timeout": 30000,
            },
            "account": {"storage_state_path": "storage_state.json"},
            "monitoring": {"enabled": True},
            "notification": {"enabled": False},
        }

    @pytest.fixture
    def invalid_config(self):
        """创建无效的配置数据"""
        return {
            "search": {
                "desktop_count": -5,  # 无效值
                "mobile_count": "invalid",  # 错误类型
                "wait_interval": {
                    "min": 10,  # min > max
                    "max": 5,
                },
            },
            "browser": {
                "headless": "not_boolean",  # 错误类型
                "prevent_focus": "invalid_value",  # 无效值
                "slow_mo": -10,  # 无效值
                "timeout": 1000,  # 太小
            },
            # 缺少必需的 account 节
        }

    def test_init(self, validator):
        """测试初始化"""
        assert validator is not None
        assert len(validator.validation_rules) > 0
        assert "search.desktop_count" in validator.validation_rules
        assert "browser.headless" in validator.validation_rules

    def test_validate_config_valid(self, validator, valid_config):
        """测试配置验证 - 有效配置"""
        is_valid, errors, warnings = validator.validate_config(valid_config)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_config_invalid(self, validator, invalid_config):
        """测试配置验证 - 无效配置"""
        is_valid, errors, warnings = validator.validate_config(invalid_config)

        assert is_valid is False
        assert len(errors) > 0

        # 检查特定错误
        error_messages = " ".join(errors)
        assert "缺少必需的配置节: 'account'" in error_messages
        assert "类型错误" in error_messages or "值过小" in error_messages

    def test_validate_required_fields_missing_section(self, validator):
        """测试必需字段验证 - 缺少配置节"""
        config = {"search": {}}  # 缺少 browser 和 account

        validator._validate_required_fields(config)

        assert len(validator.errors) >= 2
        assert any("缺少必需的配置节: 'browser'" in error for error in validator.errors)
        assert any("缺少必需的配置节: 'account'" in error for error in validator.errors)

    def test_validate_field_types_and_ranges_type_error(self, validator):
        """测试字段类型和范围验证 - 类型错误"""
        config = {
            "search": {"desktop_count": "not_a_number"},
            "browser": {"headless": "not_boolean"},
            "account": {},
        }

        validator._validate_field_types_and_ranges(config)

        assert len(validator.errors) >= 2
        error_messages = " ".join(validator.errors)
        assert "类型错误" in error_messages

    def test_validate_field_types_and_ranges_value_error(self, validator):
        """测试字段类型和范围验证 - 值错误"""
        config = {
            "search": {"desktop_count": -5, "mobile_count": 100},
            "browser": {"slow_mo": -10, "timeout": 1000},
            "account": {},
        }

        validator._validate_field_types_and_ranges(config)

        assert len(validator.errors) >= 2
        error_messages = " ".join(validator.errors)
        assert "值过小" in error_messages or "值过大" in error_messages

    def test_validate_field_types_and_ranges_allowed_values(self, validator):
        """测试字段类型和范围验证 - 允许值检查"""
        config = {"search": {}, "browser": {"prevent_focus": "invalid_value"}, "account": {}}

        validator._validate_field_types_and_ranges(config)

        assert len(validator.errors) >= 1
        assert any("值无效" in error for error in validator.errors)

    def test_validate_logical_consistency_wait_time(self, validator):
        """测试逻辑一致性验证 - 等待时间"""
        config = {
            "search": {
                "wait_interval": {"min": 10, "max": 5}  # min > max
            },
            "browser": {},
            "account": {},
        }

        validator._validate_logical_consistency(config)

        assert len(validator.errors) >= 1
        assert any("等待时间配置错误" in error for error in validator.errors)

    def test_validate_logical_consistency_search_counts(self, validator):
        """测试逻辑一致性验证 - 搜索次数"""
        config = {"search": {"desktop_count": 40, "mobile_count": 30}, "browser": {}, "account": {}}

        validator._validate_logical_consistency(config)

        assert len(validator.warnings) >= 2
        warning_messages = " ".join(validator.warnings)
        assert "超过推荐值" in warning_messages

    def test_validate_logical_consistency_headless_prevent_focus(self, validator):
        """测试逻辑一致性验证 - 无头模式与防焦点"""
        config = {
            "search": {},
            "browser": {"headless": True, "prevent_focus": "enhanced"},
            "account": {},
        }

        validator._validate_logical_consistency(config)

        assert len(validator.warnings) >= 1
        assert any("无头模式下防焦点设置无效" in warning for warning in validator.warnings)

    @patch("os.path.exists")
    def test_validate_file_paths_missing_file(self, mock_exists, validator):
        """测试文件路径验证 - 文件不存在"""
        mock_exists.return_value = False

        config = {"search": {"search_terms_file": "nonexistent.txt"}, "browser": {}, "account": {}}

        validator._validate_file_paths(config)

        assert len(validator.warnings) >= 1
        assert any("搜索词文件不存在" in warning for warning in validator.warnings)

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("os.path.dirname")
    def test_validate_file_paths_create_log_dir(
        self, mock_dirname, mock_exists, mock_makedirs, validator
    ):
        """测试文件路径验证 - 创建日志目录"""
        mock_dirname.return_value = "logs"
        mock_exists.side_effect = lambda path: path != "logs"  # logs目录不存在

        config = {"search": {}, "browser": {}, "account": {}, "logging": {"file": "logs/test.log"}}

        validator._validate_file_paths(config)

        mock_makedirs.assert_called_once_with("logs", exist_ok=True)
        assert any("已自动创建日志目录" in suggestion for suggestion in validator.suggestions)

    def test_validate_notification_config_disabled(self, validator):
        """测试通知配置验证 - 禁用状态"""
        config = {"search": {}, "browser": {}, "account": {}, "notification": {"enabled": False}}

        validator._validate_notification_config(config)

        # 禁用状态下不应该有错误
        assert len(validator.errors) == 0

    def test_validate_notification_config_enabled_no_services(self, validator):
        """测试通知配置验证 - 启用但无服务"""
        config = {
            "search": {},
            "browser": {},
            "account": {},
            "notification": {
                "enabled": True,
                "telegram": {"enabled": False},
                "serverchan": {"enabled": False},
                "whatsapp": {"enabled": False},
            },
        }

        validator._validate_notification_config(config)

        assert len(validator.warnings) >= 1
        assert any("没有配置任何通知服务" in warning for warning in validator.warnings)

    def test_validate_notification_config_telegram_missing_fields(self, validator):
        """测试通知配置验证 - Telegram缺少字段"""
        config = {
            "search": {},
            "browser": {},
            "account": {},
            "notification": {
                "enabled": True,
                "telegram": {"enabled": True},  # 缺少 bot_token 和 chat_id
            },
        }

        validator._validate_notification_config(config)

        assert len(validator.errors) >= 2
        error_messages = " ".join(validator.errors)
        assert "缺少bot_token" in error_messages
        assert "缺少chat_id" in error_messages

    def test_generate_optimization_suggestions(self, validator):
        """测试优化建议生成"""
        config = {
            "search": {"wait_interval": {"max": 3}},  # 太短
            "browser": {"slow_mo": 500},  # 太高
            "account": {},
            "monitoring": {"enabled": False},  # 未启用
        }

        validator._generate_optimization_suggestions(config)

        assert len(validator.suggestions) >= 3
        suggestion_messages = " ".join(validator.suggestions)
        assert "操作延迟" in suggestion_messages
        assert "最大等待时间" in suggestion_messages
        assert "状态监控" in suggestion_messages

    def test_get_nested_value(self, validator):
        """测试嵌套值获取"""
        data = {"level1": {"level2": {"value": "test"}}}

        result = validator._get_nested_value(data, "level1.level2.value")
        assert result == "test"

        result = validator._get_nested_value(data, "nonexistent.path")
        assert result is None

    def test_set_nested_value(self, validator):
        """测试嵌套值设置"""
        data = {}

        validator._set_nested_value(data, "level1.level2.value", "test")

        assert data["level1"]["level2"]["value"] == "test"

    def test_fix_common_issues(self, validator, invalid_config):
        """测试常见问题自动修复"""
        fixed_config = validator.fix_common_issues(invalid_config)

        # 检查等待时间是否被修复
        assert fixed_config["search"]["wait_interval"]["min"] == 2
        assert fixed_config["search"]["wait_interval"]["max"] == 5

        # 检查防焦点配置是否被修复
        assert fixed_config["browser"]["prevent_focus"] == "enhanced"

    def test_get_validation_report(self, validator):
        """测试验证报告生成"""
        validator.errors = ["错误1", "错误2"]
        validator.warnings = ["警告1"]
        validator.suggestions = ["建议1"]

        report = validator.get_validation_report()

        assert "配置验证报告" in report
        assert "错误1" in report
        assert "警告1" in report
        assert "建议1" in report
        assert "❌ 错误 (2 个)" in report
        assert "⚠️  警告 (1 个)" in report
        assert "💡 建议 (1 个)" in report

    def test_get_validation_report_no_issues(self, validator):
        """测试验证报告生成 - 无问题"""
        validator.errors = []
        validator.warnings = []
        validator.suggestions = []

        report = validator.get_validation_report()

        assert "✅ 配置验证通过，没有发现问题" in report

    @patch("src.infrastructure.config_manager.ConfigManager")
    def test_validate_config_file_success(self, mock_config_manager):
        """测试配置文件验证 - 成功"""
        mock_config = Mock()
        mock_config.config = {"search": {}, "browser": {}, "account": {}}
        mock_config_manager.return_value = mock_config

        is_valid, report = ConfigValidator.validate_config_file("test_config.yaml")

        assert is_valid is True
        assert "配置验证报告" in report

    def test_validate_config_file_failure(self):
        """测试配置文件验证 - 失败（使用无效配置）"""
        with patch("src.infrastructure.config_manager.ConfigManager") as mock_cm:
            mock_instance = Mock()
            mock_instance.config = {"invalid": "config"}
            mock_cm.return_value = mock_instance

            is_valid, report = ConfigValidator.validate_config_file("invalid_config.yaml")

            assert "配置验证报告" in report


if __name__ == "__main__":
    pytest.main([__file__])
