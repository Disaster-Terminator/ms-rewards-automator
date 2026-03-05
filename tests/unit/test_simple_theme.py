"""
SimpleThemeManager单元测试
测试简化版主题管理器的各种功能
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.simple_theme import SimpleThemeManager


class TestSimpleThemeManager:
    """SimpleThemeManager测试类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": "logs/theme_state.json",
        }.get(key, default)
        return config

    def test_init_with_config(self, mock_config):
        """测试使用配置初始化"""
        theme_manager = SimpleThemeManager(mock_config)

        assert theme_manager.enabled == True
        assert theme_manager.preferred_theme == "dark"
        assert theme_manager.persistence_enabled == True
        assert theme_manager.theme_state_file == "logs/theme_state.json"

    def test_init_without_config(self):
        """测试不使用配置初始化"""
        theme_manager = SimpleThemeManager(None)

        assert theme_manager.enabled == False
        assert theme_manager.preferred_theme == "dark"
        assert theme_manager.persistence_enabled == False
        assert theme_manager.theme_state_file == "logs/theme_state.json"

    def test_init_with_custom_config(self):
        """测试使用自定义配置初始化"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": False,
            "bing_theme.theme": "light",
            "bing_theme.persistence_enabled": False,
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        assert theme_manager.enabled == False
        assert theme_manager.preferred_theme == "light"
        assert theme_manager.persistence_enabled == False

    async def test_set_theme_cookie_dark(self, mock_config):
        """测试设置暗色主题Cookie"""
        theme_manager = SimpleThemeManager(mock_config)

        mock_context = Mock()
        mock_context.add_cookies = AsyncMock()

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result == True
        assert mock_context.add_cookies.called
        cookies = mock_context.add_cookies.call_args[0][0]
        assert len(cookies) == 1
        assert cookies[0]["name"] == "SRCHHPGUSR"
        assert cookies[0]["value"] == "WEBTHEME=1"  # dark = 1

    async def test_set_theme_cookie_light(self, mock_config):
        """测试设置亮色主题Cookie"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "light",
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        mock_context = Mock()
        mock_context.add_cookies = AsyncMock()

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result == True
        cookies = mock_context.add_cookies.call_args[0][0]
        assert cookies[0]["value"] == "WEBTHEME=0"  # light = 0

    async def test_set_theme_cookie_disabled(self):
        """测试主题管理器禁用时设置Cookie"""
        config = Mock()
        config.get.return_value = False

        theme_manager = SimpleThemeManager(config)

        mock_context = Mock()
        result = await theme_manager.set_theme_cookie(mock_context)

        assert result == True
        assert not mock_context.add_cookies.called

    async def test_set_theme_cookie_exception(self, mock_config):
        """测试设置Cookie时发生异常"""
        theme_manager = SimpleThemeManager(mock_config)

        mock_context = Mock()
        mock_context.add_cookies.side_effect = Exception("Network error")

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result == False

    async def test_save_theme_state_enabled(self, mock_config, tmp_path):
        """测试启用持久化时保存主题状态"""
        theme_file = tmp_path / "test_theme.json"
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = await theme_manager.save_theme_state("dark")

        assert result == True
        assert theme_file.exists()

        import json
        with open(theme_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["theme"] == "dark"
            assert "timestamp" in data

    async def test_save_theme_state_disabled(self, mock_config):
        """测试禁用持久化时保存主题状态"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": False,
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = await theme_manager.save_theme_state("dark")

        assert result == True  # 禁用时返回True

    async def test_load_theme_state_enabled(self, mock_config, tmp_path):
        """测试启用持久化时加载主题状态"""
        theme_file = tmp_path / "test_theme.json"
        import json
        with open(theme_file, 'w', encoding='utf-8') as f:
            json.dump({"theme": "dark", "timestamp": 1234567890}, f)

        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = await theme_manager.load_theme_state()

        assert result == "dark"

    async def test_load_theme_state_disabled(self, mock_config):
        """测试禁用持久化时加载主题状态"""
        theme_manager = SimpleThemeManager(mock_config)

        result = await theme_manager.load_theme_state()

        assert result is None

    async def test_load_theme_state_file_not_exists(self, mock_config, tmp_path):
        """测试文件不存在时加载主题状态"""
        theme_file = tmp_path / "nonexistent.json"
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = await theme_manager.load_theme_state()

        assert result is None