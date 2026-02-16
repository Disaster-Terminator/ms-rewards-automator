"""
ConfigManager 属性测试
使用 Hypothesis 进行基于属性的测试
"""

import tempfile
import os
import yaml
from hypothesis import given, strategies as st, settings
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config_manager import ConfigManager


# 定义策略
valid_log_levels = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
positive_integers = st.integers(min_value=1, max_value=50)
positive_floats = st.floats(min_value=1.0, max_value=30.0)


@given(
    desktop_count=positive_integers,
    mobile_count=positive_integers,
    wait_min=positive_floats,
    wait_max=positive_floats,
    log_level=valid_log_levels
)
@settings(max_examples=100)
def test_property_config_completeness(desktop_count, mobile_count, wait_min, wait_max, log_level):
    """
    属性 15: 配置文件完整性
    验证需求: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    
    属性: 对于任何有效的配置值，ConfigManager 应该能够正确加载并提供所有必需的配置项
    """
    # 确保 wait_min < wait_max 且 wait_min >= 1
    if wait_min >= wait_max:
        wait_max = wait_min + 1.0
    
    config_data = {
        "search": {
            "desktop_count": desktop_count,
            "mobile_count": mobile_count,
            "wait_interval": {
                "min": wait_min,
                "max": wait_max
            }
        },
        "logging": {
            "level": log_level
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        manager = ConfigManager(config_path)
        
        # 验证所有配置项都可以访问
        assert manager.get("search.desktop_count") == desktop_count
        assert manager.get("search.mobile_count") == mobile_count
        # wait_interval 从字典转换为整数中间值
        wait_interval = manager.get("search.wait_interval")
        assert isinstance(wait_interval, (int, float))
        assert manager.get("logging.level") == log_level
        
        # 验证默认值仍然存在
        assert manager.get("browser.headless") is not None
        assert manager.get("account.storage_state_path") is not None
        
        # 验证配置有效性
        assert manager.validate_config() is True
        
    finally:
        os.unlink(config_path)


@given(
    key_parts=st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))), min_size=1, max_size=3)
)
@settings(max_examples=50)
def test_property_nested_key_access(key_parts):
    """
    属性: 嵌套键访问的一致性
    
    属性: 对于任何不存在的嵌套键，get 方法应该返回 None 或指定的默认值
    """
    manager = ConfigManager("nonexistent_config.yaml")
    
    # 构建嵌套键，添加前缀确保不会匹配默认配置中的键
    nested_key = "nonexistent_test_prefix." + ".".join(key_parts)
    
    # 不存在的键应该返回 None
    assert manager.get(nested_key) is None
    
    # 使用默认值
    default_value = "test_default"
    assert manager.get(nested_key, default_value) == default_value


@given(
    desktop_count=st.integers(min_value=1, max_value=50),
    mobile_count=st.integers(min_value=1, max_value=50)
)
@settings(max_examples=50)
def test_property_config_persistence(desktop_count, mobile_count):
    """
    属性: 配置持久化一致性
    
    属性: 写入配置文件的值应该能够被正确读取
    """
    config_data = {
        "search": {
            "desktop_count": desktop_count,
            "mobile_count": mobile_count
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        # 第一次加载
        manager1 = ConfigManager(config_path)
        value1_desktop = manager1.get("search.desktop_count")
        value1_mobile = manager1.get("search.mobile_count")
        
        # 第二次加载（模拟重启）
        manager2 = ConfigManager(config_path)
        value2_desktop = manager2.get("search.desktop_count")
        value2_mobile = manager2.get("search.mobile_count")
        
        # 两次加载的值应该相同
        assert value1_desktop == value2_desktop == desktop_count
        assert value1_mobile == value2_mobile == mobile_count
        
    finally:
        os.unlink(config_path)


@given(
    wait_min=st.floats(min_value=1.0, max_value=30.0),
    wait_max=st.floats(min_value=1.0, max_value=30.0)
)
@settings(max_examples=50)
def test_property_wait_interval_validation(wait_min, wait_max):
    """
    属性: 等待间隔验证
    
    属性: wait_interval 字典会被转换为整数中间值，验证应该总是通过
    """
    config_data = {
        "search": {
            "wait_interval": {
                "min": wait_min,
                "max": wait_max
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        manager = ConfigManager(config_path)
        is_valid = manager.validate_config()
        
        # ConfigManager 会将 wait_interval 从字典转换为整数中间值
        # 所以验证应该总是通过（因为转换后的值是有效的）
        assert is_valid == True
        
        # 验证转换后的值
        wait_interval = manager.get("search.wait_interval")
        assert isinstance(wait_interval, (int, float))
        
    finally:
        os.unlink(config_path)
