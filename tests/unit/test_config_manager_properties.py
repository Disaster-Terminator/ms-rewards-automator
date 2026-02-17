"""
ConfigManager 属性测试
使用 Hypothesis 进行基于属性的测试
"""

import os
import sys
import tempfile
from pathlib import Path

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config_manager import ConfigManager

valid_log_levels = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

MINIMAL_VALID_CONFIG = {
    "search": {"desktop_count": 30, "mobile_count": 20},
    "browser": {"headless": True},
    "account": {"storage_state_path": "test.json"},
}


@given(
    desktop_count=st.integers(min_value=1, max_value=50),
    mobile_count=st.integers(min_value=1, max_value=50),
    log_level=valid_log_levels,
)
@settings(max_examples=50)
def test_property_config_completeness(desktop_count, mobile_count, log_level):
    """
    属性 15: 配置文件完整性
    验证需求: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7

    属性: 对于任何有效的配置值，ConfigManager 应该能够正确加载并提供所有必需的配置项
    """
    config_data = {
        **MINIMAL_VALID_CONFIG,
        "search": {
            "desktop_count": desktop_count,
            "mobile_count": mobile_count,
        },
        "logging": {"level": log_level},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)

        assert manager.get("search.desktop_count") == desktop_count
        assert manager.get("search.mobile_count") == mobile_count
        assert manager.get("logging.level") == log_level

        assert manager.get("browser.headless") is not None
        assert manager.get("account.storage_state_path") is not None

        assert manager.validate_config()

    finally:
        os.unlink(config_path)


@given(
    key_parts=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
        min_size=2,
        max_size=4,
    )
)
@settings(max_examples=50)
def test_property_nested_key_access(key_parts):
    """
    属性: 嵌套键访问的一致性

    属性: 对于任何不存在的嵌套键，get 方法应该返回 None 或指定的默认值
    """
    manager = ConfigManager("nonexistent_config.yaml")

    nested_key = "nonexistent." + ".".join(key_parts)

    assert manager.get(nested_key) is None

    default_value = "test_default"
    assert manager.get(nested_key, default_value) == default_value


@given(
    desktop_count=st.integers(min_value=1, max_value=50),
    mobile_count=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=50)
def test_property_config_persistence(desktop_count, mobile_count):
    """
    属性: 配置持久化一致性

    属性: 写入配置文件的值应该能够被正确读取
    """
    config_data = {"search": {"desktop_count": desktop_count, "mobile_count": mobile_count}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        manager1 = ConfigManager(config_path)
        value1_desktop = manager1.get("search.desktop_count")
        value1_mobile = manager1.get("search.mobile_count")

        manager2 = ConfigManager(config_path)
        value2_desktop = manager2.get("search.desktop_count")
        value2_mobile = manager2.get("search.mobile_count")

        assert value1_desktop == value2_desktop == desktop_count
        assert value1_mobile == value2_mobile == mobile_count

    finally:
        os.unlink(config_path)


@given(wait_interval=st.integers(min_value=1, max_value=30))
@settings(max_examples=30)
def test_property_wait_interval_single_value(wait_interval):
    """
    属性: 单个等待间隔值向后兼容

    属性: 单个 wait_interval 值应该被自动转换为 dict 格式
    """
    config_data = {
        **MINIMAL_VALID_CONFIG,
        "search": {"wait_interval": wait_interval},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)
        # int 格式会被自动转换为 dict 格式
        result = manager.get("search.wait_interval")
        assert result == {"min": wait_interval, "max": wait_interval + 10}
        assert manager.validate_config()

    finally:
        os.unlink(config_path)
