"""
SimpleThemeManager单元测试
测试简化版主题管理器的各种功能
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ui.simple_theme import SimpleThemeManager


class TestSimpleThemeManager:
    """SimpleThemeManager测试类"""

    @pytest.fixture
    def mock_config(self) -> Any:
        """模拟配置"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": "logs/theme_state.json",
        }.get(key, default)
        return config

    def test_init_with_config(self, mock_config: Any) -> None:
        """测试使用配置初始化"""
        theme_manager = SimpleThemeManager(mock_config)

        assert theme_manager.enabled is True
        assert theme_manager.preferred_theme == "dark"
        assert theme_manager.persistence_enabled is True
        assert theme_manager.theme_state_file == "logs/theme_state.json"

    def test_init_without_config(self) -> None:
        """测试不使用配置初始化"""
        theme_manager = SimpleThemeManager(None)

        assert theme_manager.enabled is False
        assert theme_manager.preferred_theme == "dark"
        assert theme_manager.persistence_enabled is False
        assert theme_manager.theme_state_file == "logs/theme_state.json"

    def test_init_with_custom_config(self) -> None:
        """测试使用自定义配置初始化"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": False,
            "bing_theme.theme": "light",
            "bing_theme.persistence_enabled": False,
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        assert theme_manager.enabled is False
        assert theme_manager.preferred_theme == "light"
        assert theme_manager.persistence_enabled is False

    async def test_set_theme_cookie_dark(self, mock_config) -> None:
        """测试设置暗色主题Cookie"""
        theme_manager = SimpleThemeManager(mock_config)

        mock_context = Mock()
        mock_context.cookies = AsyncMock(return_value=[])
        mock_context.add_cookies = AsyncMock()

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result is True
        assert mock_context.add_cookies.called
        cookies = mock_context.add_cookies.call_args[0][0]
        assert len(cookies) == 1
        assert cookies[0]["name"] == "SRCHHPGUSR"
        assert cookies[0]["value"] == "WEBTHEME=1"  # dark = 1

    async def test_set_theme_cookie_light(self, mock_config) -> None:
        """测试设置亮色主题Cookie"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "light",
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        mock_context = Mock()
        mock_context.cookies = AsyncMock(return_value=[])
        mock_context.add_cookies = AsyncMock()

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result is True
        cookies = mock_context.add_cookies.call_args[0][0]
        assert cookies[0]["value"] == "WEBTHEME=0"  # light = 0

    async def test_set_theme_cookie_preserves_existing_settings(self, mock_config) -> None:
        """测试设置主题Cookie时保留现有设置"""
        theme_manager = SimpleThemeManager(mock_config)

        # 模拟现有的 Cookie（包含其他设置）
        existing_cookie = {
            "name": "SRCHHPGUSR",
            "value": "NRSLT=50;OBHLTH=1;WEBTHEME=0",  # 原本是亮色主题
            "domain": ".bing.com",
        }
        mock_context = Mock()
        mock_context.cookies = AsyncMock(return_value=[existing_cookie])
        mock_context.add_cookies = AsyncMock()

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result is True
        cookies = mock_context.add_cookies.call_args[0][0]
        assert cookies[0]["name"] == "SRCHHPGUSR"
        # 应该保留 NRSLT 和 OBHLTH，只修改 WEBTHEME
        assert "NRSLT=50" in cookies[0]["value"]
        assert "OBHLTH=1" in cookies[0]["value"]
        assert "WEBTHEME=1" in cookies[0]["value"]  # dark = 1

    async def test_set_theme_cookie_disabled(self) -> None:
        """测试主题管理器禁用时设置Cookie"""
        config = Mock()
        config.get.return_value = False

        theme_manager = SimpleThemeManager(config)

        mock_context = Mock()
        result = await theme_manager.set_theme_cookie(mock_context)

        assert result is True
        assert not mock_context.add_cookies.called

    async def test_set_theme_cookie_exception(self, mock_config) -> None:
        """测试设置Cookie时发生异常"""
        theme_manager = SimpleThemeManager(mock_config)

        mock_context = Mock()
        mock_context.cookies = AsyncMock(side_effect=Exception("Network error"))

        result = await theme_manager.set_theme_cookie(mock_context)

        assert result is False

    def test_save_theme_state_enabled(self, mock_config, tmp_path) -> None:
        """测试启用持久化时保存主题状态"""
        theme_file = tmp_path / "test_theme.json"
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = theme_manager.save_theme_state("dark")

        assert result is True
        assert theme_file.exists()

        import json

        with open(theme_file, encoding="utf-8") as f:
            data = json.load(f)
            assert data["theme"] == "dark"
            assert "timestamp" in data

    def test_save_theme_state_disabled(self, mock_config) -> None:
        """测试禁用持久化时保存主题状态"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": False,
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = theme_manager.save_theme_state("dark")

        assert result is True  # 禁用时返回True

    def test_load_theme_state_enabled(self, mock_config, tmp_path) -> None:
        """测试启用持久化时加载主题状态"""
        theme_file = tmp_path / "test_theme.json"
        import json

        with open(theme_file, "w", encoding="utf-8") as f:
            json.dump({"theme": "dark", "timestamp": 1234567890}, f)

        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = theme_manager.load_theme_state()

        assert result == "dark"

    def test_load_theme_state_disabled(self, mock_config) -> None:
        """测试禁用持久化时加载主题状态"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": False,
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = theme_manager.load_theme_state()

        assert result is None

    def test_load_theme_state_file_not_exists(self, mock_config, tmp_path) -> None:
        """测试文件不存在时加载主题状态"""
        theme_file = tmp_path / "nonexistent.json"
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": str(theme_file),
        }.get(key, default)

        theme_manager = SimpleThemeManager(config)

        result = theme_manager.load_theme_state()

        assert result is None
