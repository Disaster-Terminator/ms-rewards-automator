"""
ConfigManager 单元测试
"""

import os
import sys
import tempfile
from pathlib import Path

import yaml

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager 单元测试类"""

    def test_load_valid_config(self):
        """测试加载有效配置文件"""
        config_data = {"search": {"desktop_count": 25, "mobile_count": 15}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            assert manager.get("search.desktop_count") == 25
            assert manager.get("search.mobile_count") == 15
            # 默认值应该被保留
            assert not manager.get("browser.headless")
        finally:
            os.unlink(config_path)

    def test_missing_config_uses_defaults(self):
        """测试缺失配置项使用默认值"""
        manager = ConfigManager("nonexistent_config.yaml")

        assert manager.get("search.desktop_count") == 20
        assert manager.get("search.mobile_count") == 0
        assert not manager.get("browser.headless")

    def test_nested_config_access(self):
        """测试嵌套配置项访问"""
        manager = ConfigManager("nonexistent_config.yaml")

        # 测试嵌套访问
        assert manager.get("search.wait_interval") == {"min": 5, "max": 15}
        assert not manager.get("login.auto_login.enabled")
        assert not manager.get("browser.headless")

    def test_invalid_config_error_handling(self):
        """测试无效配置文件错误处理"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            assert manager.get("search.desktop_count") == 20
        finally:
            os.unlink(config_path)

    def test_get_with_default(self):
        """测试 get 方法的默认值参数"""
        manager = ConfigManager("nonexistent_config.yaml")

        # 不存在的键应该返回默认值
        assert manager.get("nonexistent.key", "default_value") == "default_value"
        assert manager.get("another.missing.key", 42) == 42

    def test_validate_config_valid(self):
        """测试有效配置的验证"""
        manager = ConfigManager("nonexistent_config.yaml")
        assert manager.validate_config()

    def test_validate_config_invalid_desktop_count(self):
        """测试无效的 desktop_count"""
        config_data = {
            "search": {
                "desktop_count": -5  # 无效值
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            assert not manager.validate_config()
        finally:
            os.unlink(config_path)

    def test_validate_config_invalid_wait_interval(self):
        """测试 wait_interval 的向后兼容转换（int -> dict）"""
        # 当 wait_interval 是 int 格式时，会自动转换为 dict 格式
        config_data = {"search": {"wait_interval": 5}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            # int 格式会被转换为 dict 格式
            assert manager.get("search.wait_interval") == {"min": 5, "max": 15}
            assert manager.validate_config()
        finally:
            os.unlink(config_path)

    def test_validate_config_invalid_log_level(self):
        """测试无效的日志级别"""
        config_data = {"logging": {"level": "INVALID_LEVEL"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            assert not manager.validate_config()
        finally:
            os.unlink(config_path)

    def test_config_merge(self):
        """测试配置合并功能"""
        config_data = {
            "search": {
                "desktop_count": 40  # 覆盖默认值
                # mobile_count 未指定，应使用默认值
            },
            "browser": {
                "headless": True  # 覆盖默认值
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            assert manager.get("search.desktop_count") == 40
            assert manager.get("browser.headless")
            assert manager.get("search.mobile_count") == 0
            assert manager.get("browser.slow_mo") == 100
        finally:
            os.unlink(config_path)
