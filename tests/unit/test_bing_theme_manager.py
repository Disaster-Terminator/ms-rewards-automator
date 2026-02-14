"""
BingThemeManager单元测试
测试Bing主题管理器的各种功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.bing_theme_manager import BingThemeManager


class TestBingThemeManager:
    """BingThemeManager测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True
        }.get(key, default)
        return config
    
    @pytest.fixture
    def theme_manager(self, mock_config):
        """创建主题管理器实例"""
        return BingThemeManager(mock_config)
    
    @pytest.fixture
    def mock_page(self):
        """模拟Playwright页面"""
        page = AsyncMock()
        page.url = "https://www.bing.com"
        page.context = AsyncMock()
        return page
    
    def test_init_with_config(self, mock_config):
        """测试使用配置初始化"""
        manager = BingThemeManager(mock_config)
        
        assert manager.enabled is True
        assert manager.preferred_theme == "dark"
        assert manager.force_theme is True
        assert manager.config == mock_config
    
    def test_init_without_config(self):
        """测试不使用配置初始化"""
        manager = BingThemeManager()
        
        assert manager.enabled is True
        assert manager.preferred_theme == "dark"
        assert manager.force_theme is True
        assert manager.config is None
    
    def test_init_with_custom_config(self):
        """测试自定义配置初始化"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": False,
            "bing_theme.theme": "light",
            "bing_theme.force_theme": False
        }.get(key, default)
        
        manager = BingThemeManager(config)
        
        assert manager.enabled is False
        assert manager.preferred_theme == "light"
        assert manager.force_theme is False
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_dark_by_class(self, theme_manager, mock_page):
        """测试通过CSS类检测深色主题"""
        # 模拟CSS类检测成功
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value=None):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value=None):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_by_style(self, theme_manager, mock_page):
        """测试通过样式检测主题"""
        # 模拟只有样式检测成功
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value=None):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value=None):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_by_cookie(self, theme_manager, mock_page):
        """测试通过Cookie检测主题"""
        # 模拟只有Cookie检测成功
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value=None):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value=None):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="dark"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_light_cookie(self, theme_manager, mock_page):
        """测试通过Cookie检测浅色主题"""
        # 模拟Cookie检测到浅色主题
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value=None):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value=None):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="light"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_default_light(self, theme_manager, mock_page):
        """测试默认返回浅色主题"""
        # 模拟所有检测方法都失败
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value=None):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value=None):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value=None):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_exception(self, theme_manager, mock_page):
        """测试检测主题时发生异常"""
        # 模拟检测方法抛出异常
        with patch.object(theme_manager, '_detect_theme_by_css_classes', side_effect=Exception("CSS error")):
            result = await theme_manager.detect_current_theme(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_theme_disabled(self, mock_config, mock_page):
        """测试主题管理禁用时的行为"""
        mock_config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": False,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True
        }.get(key, default)
        
        manager = BingThemeManager(mock_config)
        result = await manager.set_theme(mock_page, "dark")
        
        assert result is True
        # 不应该调用任何页面操作
        mock_page.goto.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_theme_already_correct(self, theme_manager, mock_page):
        """测试主题已经正确时的行为"""
        # 模拟当前主题已经是目标主题
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is True
        # 不应该尝试设置主题
        mock_page.goto.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_theme_by_url_success(self, theme_manager, mock_page):
        """测试通过URL成功设置主题"""
        # 模拟当前主题检测
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["light", "dark"]):
            mock_page.url = "https://www.bing.com"
            
            result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is True
        mock_page.goto.assert_called_once()
        # 验证URL包含主题参数
        called_url = mock_page.goto.call_args[0][0]
        assert "SRCHHPGUSR=THEME=1" in called_url
    
    @pytest.mark.asyncio
    async def test_set_theme_by_url_with_existing_params(self, theme_manager, mock_page):
        """测试在已有参数的URL上设置主题"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["light", "dark"]):
            mock_page.url = "https://www.bing.com?SRCHHPGUSR=THEME:0&other=value"
            
            result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is True
        mock_page.goto.assert_called_once()
        # 验证URL更新了主题参数
        called_url = mock_page.goto.call_args[0][0]
        assert "THEME=1" in called_url or "THEME:1" in called_url
    
    @pytest.mark.asyncio
    async def test_set_theme_by_cookie_success(self, theme_manager, mock_page):
        """测试通过Cookie成功设置主题"""
        # 模拟URL方法失败，Cookie方法成功
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["light", "light", "dark"]):
            with patch.object(theme_manager, '_set_theme_by_url', return_value=False):
                result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is True
        # 验证设置了多个Cookie变体（增强的实现）
        assert mock_page.context.add_cookies.call_count > 1
        # 验证页面被重新加载（可能多次，因为有多种方法尝试）
        assert mock_page.reload.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_set_theme_all_methods_fail(self, theme_manager, mock_page):
        """测试所有设置方法都失败"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="light"):
            with patch.object(theme_manager, '_set_theme_by_url', return_value=False):
                with patch.object(theme_manager, '_set_theme_by_cookie', return_value=False):
                    with patch.object(theme_manager, '_set_theme_by_settings', return_value=False):
                        result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_theme_exception(self, theme_manager, mock_page):
        """测试设置主题时发生异常"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=Exception("Detection failed")):
            result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_disabled(self, mock_config, mock_page):
        """测试主题管理禁用时的搜索前检查"""
        mock_config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": False,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True
        }.get(key, default)
        
        manager = BingThemeManager(mock_config)
        result = await manager.ensure_theme_before_search(mock_page)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_force_disabled(self, mock_config, mock_page):
        """测试强制主题禁用时的搜索前检查"""
        mock_config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": False
        }.get(key, default)
        
        manager = BingThemeManager(mock_config)
        result = await manager.ensure_theme_before_search(mock_page)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_correct_theme(self, theme_manager, mock_page):
        """测试主题已正确时的搜索前检查"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager.ensure_theme_before_search(mock_page)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_needs_change(self, theme_manager, mock_page):
        """测试需要更改主题时的搜索前检查"""
        # 模拟持久化被禁用，这样只会调用一次 set_theme
        theme_manager.persistence_enabled = False
        
        with patch.object(theme_manager, 'detect_current_theme', new_callable=AsyncMock, return_value="light"):
            with patch.object(theme_manager, 'set_theme', new_callable=AsyncMock, return_value=True) as mock_set:
                result = await theme_manager.ensure_theme_before_search(mock_page)
        
        assert result is True
        # 应该至少调用一次 set_theme
        assert mock_set.call_count >= 1
        # 验证调用参数
        mock_set.assert_any_call(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_exception(self, theme_manager, mock_page):
        """测试搜索前检查发生异常"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=Exception("Detection failed")):
            result = await theme_manager.ensure_theme_before_search(mock_page)
        
        # 异常不应该阻止搜索
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_success(self, theme_manager, mock_page):
        """测试主题持久化验证成功"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["dark", "dark"]):
            result = await theme_manager.verify_theme_persistence(mock_page)
        
        assert result is True
        mock_page.reload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_failure(self, theme_manager, mock_page):
        """测试主题持久化验证失败"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["dark", "light"]):
            result = await theme_manager.verify_theme_persistence(mock_page)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_exception(self, theme_manager, mock_page):
        """测试主题持久化验证异常"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=Exception("Failed")):
            result = await theme_manager.verify_theme_persistence(mock_page)
        
        assert result is False
    
    def test_get_theme_config(self, theme_manager):
        """测试获取主题配置"""
        config = theme_manager.get_theme_config()
        
        expected = {
            "enabled": True,
            "preferred_theme": "dark",
            "force_theme": True,
        }
        
        assert config == expected
    
    @pytest.mark.asyncio
    async def test_set_theme_by_settings_success(self, theme_manager, mock_page):
        """测试通过设置页面成功设置主题"""
        # 模拟找到所有必需元素
        mock_settings_button = AsyncMock()
        mock_settings_button.is_visible.return_value = True
        mock_theme_option = AsyncMock()
        mock_save_button = AsyncMock()
        mock_save_button.is_visible.return_value = True
        
        mock_page.wait_for_selector.side_effect = [
            mock_settings_button,  # 设置按钮
            mock_theme_option,     # 主题选项
            mock_save_button       # 保存按钮
        ]
        
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager._set_theme_by_settings(mock_page, "dark")
        
        assert result is True
        mock_settings_button.click.assert_called_once()
        mock_theme_option.click.assert_called_once()
        mock_save_button.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_theme_by_settings_no_settings_button(self, theme_manager, mock_page):
        """测试设置页面找不到设置按钮"""
        mock_page.wait_for_selector.side_effect = Exception("Not found")
        
        result = await theme_manager._set_theme_by_settings(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_theme_by_settings_no_theme_option(self, theme_manager, mock_page):
        """测试设置页面找不到主题选项"""
        mock_settings_button = AsyncMock()
        mock_settings_button.is_visible.return_value = True
        
        mock_page.wait_for_selector.side_effect = [
            mock_settings_button,  # 设置按钮找到
            Exception("Theme option not found")  # 主题选项未找到
        ]
        
        result = await theme_manager._set_theme_by_settings(mock_page, "dark")
        
        assert result is False
        mock_settings_button.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_theme_by_settings_no_save_button(self, theme_manager, mock_page):
        """测试设置页面找不到保存按钮但主题设置成功"""
        mock_settings_button = AsyncMock()
        mock_settings_button.is_visible.return_value = True
        mock_theme_option = AsyncMock()
        
        mock_page.wait_for_selector.side_effect = [
            mock_settings_button,  # 设置按钮
            mock_theme_option,     # 主题选项
            Exception("Save button not found")  # 保存按钮未找到
        ]
        
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager._set_theme_by_settings(mock_page, "dark")
        
        assert result is True  # 即使没有保存按钮，如果主题设置成功也返回True
        mock_theme_option.click.assert_called_once()
    
    # 新增的检测方法测试
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_css_classes_dark(self, theme_manager, mock_page):
        """测试CSS类检测深色主题"""
        # 模拟找到深色主题CSS类
        mock_page.query_selector.side_effect = [Mock(), None, None]  # 第一个找到
        
        result = await theme_manager._detect_theme_by_css_classes(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_css_classes_light(self, theme_manager, mock_page):
        """测试CSS类检测浅色主题"""
        # 模拟深色主题类未找到，但找到浅色主题类
        dark_selectors_count = 11  # 深色主题选择器数量
        light_selectors_count = 9  # 浅色主题选择器数量
        
        mock_page.query_selector.side_effect = (
            [None] * dark_selectors_count +  # 深色主题选择器都未找到
            [Mock()] + [None] * (light_selectors_count - 1)  # 第一个浅色主题选择器找到
        )
        
        result = await theme_manager._detect_theme_by_css_classes(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_css_classes_none(self, theme_manager, mock_page):
        """测试CSS类检测无结果"""
        # 模拟所有选择器都未找到
        mock_page.query_selector.return_value = None
        
        result = await theme_manager._detect_theme_by_css_classes(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_computed_styles_dark(self, theme_manager, mock_page):
        """测试计算样式检测深色主题"""
        mock_page.evaluate.return_value = "dark"
        
        result = await theme_manager._detect_theme_by_computed_styles(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_computed_styles_light(self, theme_manager, mock_page):
        """测试计算样式检测浅色主题"""
        mock_page.evaluate.return_value = "light"
        
        result = await theme_manager._detect_theme_by_computed_styles(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_computed_styles_exception(self, theme_manager, mock_page):
        """测试计算样式检测异常"""
        mock_page.evaluate.side_effect = Exception("JS error")
        
        result = await theme_manager._detect_theme_by_computed_styles(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_cookies_dark_theme1(self, theme_manager, mock_page):
        """测试Cookie检测深色主题 (THEME:1)"""
        mock_page.context.cookies.return_value = [
            {"name": "SRCHHPGUSR", "value": "THEME:1&other=value"}
        ]
        
        result = await theme_manager._detect_theme_by_cookies(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_cookies_dark_theme_equals(self, theme_manager, mock_page):
        """测试Cookie检测深色主题 (THEME=1)"""
        mock_page.context.cookies.return_value = [
            {"name": "SRCHHPGUSR", "value": "THEME=1&other=value"}
        ]
        
        result = await theme_manager._detect_theme_by_cookies(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_cookies_light_theme0(self, theme_manager, mock_page):
        """测试Cookie检测浅色主题 (THEME:0)"""
        mock_page.context.cookies.return_value = [
            {"name": "SRCHHPGUSR", "value": "THEME:0&other=value"}
        ]
        
        result = await theme_manager._detect_theme_by_cookies(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_cookies_other_theme_cookie(self, theme_manager, mock_page):
        """测试其他主题Cookie检测"""
        mock_page.context.cookies.return_value = [
            {"name": "theme", "value": "dark"}
        ]
        
        result = await theme_manager._detect_theme_by_cookies(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_cookies_none(self, theme_manager, mock_page):
        """测试Cookie检测无结果"""
        mock_page.context.cookies.return_value = [
            {"name": "other_cookie", "value": "some_value"}
        ]
        
        result = await theme_manager._detect_theme_by_cookies(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_url_params_dark(self, theme_manager, mock_page):
        """测试URL参数检测深色主题"""
        mock_page.url = "https://www.bing.com?THEME=1&other=value"
        
        result = await theme_manager._detect_theme_by_url_params(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_url_params_light(self, theme_manager, mock_page):
        """测试URL参数检测浅色主题"""
        mock_page.url = "https://www.bing.com?THEME=0&other=value"
        
        result = await theme_manager._detect_theme_by_url_params(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_url_params_none(self, theme_manager, mock_page):
        """测试URL参数检测无结果"""
        mock_page.url = "https://www.bing.com?other=value"
        
        result = await theme_manager._detect_theme_by_url_params(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_storage_dark(self, theme_manager, mock_page):
        """测试存储检测深色主题"""
        mock_page.evaluate.return_value = "dark"
        
        result = await theme_manager._detect_theme_by_storage(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_storage_light(self, theme_manager, mock_page):
        """测试存储检测浅色主题"""
        mock_page.evaluate.return_value = "light"
        
        result = await theme_manager._detect_theme_by_storage(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_storage_none(self, theme_manager, mock_page):
        """测试存储检测无结果"""
        mock_page.evaluate.return_value = None
        
        result = await theme_manager._detect_theme_by_storage(mock_page)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_meta_tags_dark(self, theme_manager, mock_page):
        """测试Meta标签检测深色主题"""
        mock_page.evaluate.return_value = "dark"
        
        result = await theme_manager._detect_theme_by_meta_tags(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_meta_tags_light(self, theme_manager, mock_page):
        """测试Meta标签检测浅色主题"""
        mock_page.evaluate.return_value = "light"
        
        result = await theme_manager._detect_theme_by_meta_tags(mock_page)
        
        assert result == "light"
    
    @pytest.mark.asyncio
    async def test_detect_theme_by_meta_tags_none(self, theme_manager, mock_page):
        """测试Meta标签检测无结果"""
        mock_page.evaluate.return_value = None
        
        result = await theme_manager._detect_theme_by_meta_tags(mock_page)
        
        assert result is None
    
    def test_vote_for_theme_dark_majority(self, theme_manager):
        """测试投票机制 - 深色主题占多数"""
        detection_results = [
            ("css_classes", "dark"),
            ("computed_styles", "dark"),
            ("cookies", "light"),
            ("url_params", "dark")
        ]
        
        result = theme_manager._vote_for_theme(detection_results)
        
        assert result == "dark"
    
    def test_vote_for_theme_light_majority(self, theme_manager):
        """测试投票机制 - 浅色主题占多数"""
        detection_results = [
            ("css_classes", "light"),
            ("computed_styles", "light"),
            ("cookies", "dark"),
            ("storage", "light")
        ]
        
        result = theme_manager._vote_for_theme(detection_results)
        
        assert result == "light"
    
    def test_vote_for_theme_tie_default_light(self, theme_manager):
        """测试投票机制 - 平票时默认浅色"""
        detection_results = [
            ("css_classes", "dark"),
            ("computed_styles", "light")
        ]
        
        result = theme_manager._vote_for_theme(detection_results)
        
        assert result == "light"  # 平票时默认浅色
    
    def test_vote_for_theme_empty_results(self, theme_manager):
        """测试投票机制 - 无检测结果"""
        detection_results = []
        
        result = theme_manager._vote_for_theme(detection_results)
        
        assert result == "light"  # 默认浅色
    
    def test_vote_for_theme_weighted_voting(self, theme_manager):
        """测试投票机制 - 权重投票"""
        # CSS类权重3，存储权重1，深色主题应该获胜
        detection_results = [
            ("css_classes", "dark"),      # 权重3
            ("storage", "light"),         # 权重1
            ("meta_tags", "light")        # 权重1
        ]
        
        result = theme_manager._vote_for_theme(detection_results)
        
        assert result == "dark"  # 深色主题权重更高
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_multiple_methods_consensus(self, theme_manager, mock_page):
        """测试多种方法达成一致的主题检测"""
        # 模拟多种方法都检测到深色主题
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="dark"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                result = await theme_manager.detect_current_theme(mock_page)
        
        assert result == "dark"
    
    @pytest.mark.asyncio
    async def test_detect_current_theme_conflicting_methods(self, theme_manager, mock_page):
        """测试检测方法冲突时的投票机制"""
        # 模拟方法冲突：高权重方法检测到深色，低权重方法检测到浅色
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):  # 权重3
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):  # 权重3
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="light"):  # 权重2
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value="light"):  # 权重1
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value="light"):  # 权重1
                                result = await theme_manager.detect_current_theme(mock_page)
        
        # 深色主题权重: 3+3=6, 浅色主题权重: 2+1+1=4, 深色主题应该获胜
        assert result == "dark"
    
    # 新增的增强方法测试
    
    @pytest.mark.asyncio
    async def test_set_theme_by_localstorage_success(self, theme_manager, mock_page):
        """测试通过localStorage成功设置主题"""
        mock_page.evaluate.return_value = None  # JavaScript执行成功
        
        with patch.object(theme_manager, '_quick_theme_check', return_value=True):
            result = await theme_manager._set_theme_by_localstorage(mock_page, "dark")
        
        assert result is True
        mock_page.evaluate.assert_called_once()
        mock_page.reload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_theme_by_javascript_success(self, theme_manager, mock_page):
        """测试通过JavaScript注入成功设置主题"""
        mock_page.evaluate.return_value = True
        
        result = await theme_manager._set_theme_by_javascript(mock_page, "dark")
        
        assert result is True
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_theme_by_javascript_failure(self, theme_manager, mock_page):
        """测试JavaScript注入设置主题失败"""
        mock_page.evaluate.return_value = False
        
        result = await theme_manager._set_theme_by_javascript(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_theme_by_force_css_success(self, theme_manager, mock_page):
        """测试通过强制CSS成功设置主题"""
        mock_page.add_style_tag.return_value = None
        mock_page.evaluate.return_value = None
        
        result = await theme_manager._set_theme_by_force_css(mock_page, "dark")
        
        assert result is True
        mock_page.add_style_tag.assert_called_once()
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_theme_with_retry_success_first_attempt(self, theme_manager, mock_page):
        """测试带重试的主题设置第一次就成功"""
        with patch.object(theme_manager, 'set_theme', return_value=True) as mock_set:
            result = await theme_manager.set_theme_with_retry(mock_page, "dark", max_retries=3)
        
        assert result is True
        mock_set.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_set_theme_with_retry_success_second_attempt(self, theme_manager, mock_page):
        """测试带重试的主题设置第二次成功"""
        with patch.object(theme_manager, 'set_theme', side_effect=[False, True]) as mock_set:
            result = await theme_manager.set_theme_with_retry(mock_page, "dark", max_retries=3)
        
        assert result is True
        assert mock_set.call_count == 2
    
    @pytest.mark.asyncio
    async def test_set_theme_with_retry_all_attempts_fail(self, theme_manager, mock_page):
        """测试带重试的主题设置所有尝试都失败"""
        with patch.object(theme_manager, 'set_theme', return_value=False) as mock_set:
            result = await theme_manager.set_theme_with_retry(mock_page, "dark", max_retries=2)
        
        assert result is False
        assert mock_set.call_count == 2
    
    @pytest.mark.asyncio
    async def test_force_theme_application_success(self, theme_manager, mock_page):
        """测试强制主题应用成功"""
        # 模拟部分方法成功
        with patch.object(theme_manager, '_set_theme_by_localstorage', return_value=True):
            with patch.object(theme_manager, '_set_theme_by_javascript', return_value=True):
                with patch.object(theme_manager, '_set_theme_by_force_css', return_value=False):
                    with patch.object(theme_manager, '_set_theme_by_url', return_value=True):
                        with patch.object(theme_manager, '_set_theme_by_cookie', return_value=False):
                            result = await theme_manager.force_theme_application(mock_page, "dark")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_force_theme_application_all_fail(self, theme_manager, mock_page):
        """测试强制主题应用所有方法都失败"""
        # 模拟所有方法都失败
        with patch.object(theme_manager, '_set_theme_by_localstorage', return_value=False):
            with patch.object(theme_manager, '_set_theme_by_javascript', return_value=False):
                with patch.object(theme_manager, '_set_theme_by_force_css', return_value=False):
                    with patch.object(theme_manager, '_set_theme_by_url', return_value=False):
                        with patch.object(theme_manager, '_set_theme_by_cookie', return_value=False):
                            result = await theme_manager.force_theme_application(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_theme_status_report_success(self, theme_manager, mock_page):
        """测试获取主题状态报告成功"""
        # 模拟各种检测方法
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="dark"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
                                    mock_page.url = "https://www.bing.com"
                                    mock_page.title.return_value = "Bing"
                                    mock_page.evaluate.return_value = "Mozilla/5.0"
                                    
                                    report = await theme_manager.get_theme_status_report(mock_page)
        
        assert report["final_theme"] == "dark"
        assert report["status"] == "成功"
        assert "detection_results" in report
        assert "page_info" in report
        assert "config" in report
        assert report["page_info"]["url"] == "https://www.bing.com"
    
    @pytest.mark.asyncio
    async def test_get_theme_status_report_with_errors(self, theme_manager, mock_page):
        """测试获取主题状态报告时有错误"""
        # 模拟检测方法抛出异常
        with patch.object(theme_manager, '_detect_theme_by_css_classes', side_effect=Exception("CSS error")):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value=None):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value=None):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
                                    mock_page.url = "https://www.bing.com"
                                    mock_page.title.return_value = "Bing"
                                    mock_page.evaluate.return_value = "Mozilla/5.0"
                                    
                                    report = await theme_manager.get_theme_status_report(mock_page)
        
        assert report["final_theme"] == "dark"
        assert "错误: CSS error" in report["detection_results"]["CSS类"]
    
    def test_generate_force_theme_css_dark(self, theme_manager):
        """测试生成深色主题强制CSS"""
        css = theme_manager._generate_force_theme_css("dark")
        
        assert "background-color: #212529 !important" in css
        assert "color: #ffffff !important" in css
        assert "color-scheme: dark !important" in css
        assert "forced-dark-theme" in css
    
    def test_generate_force_theme_css_light(self, theme_manager):
        """测试生成浅色主题强制CSS"""
        css = theme_manager._generate_force_theme_css("light")
        
        assert "background-color: #ffffff !important" in css
        assert "color: #212529 !important" in css
        assert "color-scheme: light !important" in css
        assert "forced-light-theme" in css
    
    @pytest.mark.asyncio
    async def test_quick_theme_check_success(self, theme_manager, mock_page):
        """测试快速主题检查成功"""
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            result = await theme_manager._quick_theme_check(mock_page, "dark")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_quick_theme_check_failure(self, theme_manager, mock_page):
        """测试快速主题检查失败"""
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="light"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="light"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="light"):
                    result = await theme_manager._quick_theme_check(mock_page, "dark")
        
        assert result is False


class TestBingThemeManagerFailureHandling:
    """BingThemeManager失败处理测试类"""
    
    @pytest.fixture
    def theme_manager(self):
        """创建主题管理器实例"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True
        }.get(key, default)
        return BingThemeManager(config)
    
    @pytest.fixture
    def mock_page(self):
        """模拟Playwright页面"""
        page = AsyncMock()
        page.url = "https://www.bing.com"
        page.context = AsyncMock()
        page.title.return_value = "Bing"
        page.evaluate.return_value = "Mozilla/5.0"
        return page
    
    @pytest.mark.asyncio
    async def test_handle_theme_setting_failure(self, theme_manager, mock_page):
        """测试主题设置失败处理"""
        failure_details = [
            "URL参数: 方法返回失败",
            "Cookie: 设置异常: Connection error",
            "JavaScript注入: 主题设置验证失败: 期望dark, 实际light"
        ]
        
        with patch.object(theme_manager, '_generate_theme_failure_diagnostic') as mock_diagnostic:
            with patch.object(theme_manager, '_generate_failure_suggestions', return_value=["建议1", "建议2"]):
                with patch.object(theme_manager, '_save_failure_screenshot', return_value=True):
                    mock_diagnostic.return_value = {
                        "page_url": "https://www.bing.com",
                        "page_title": "Bing",
                        "current_theme": "light",
                        "target_theme": "dark"
                    }
                    
                    await theme_manager._handle_theme_setting_failure(mock_page, "dark", failure_details)
        
        # 验证调用了诊断方法
        mock_diagnostic.assert_called_once_with(mock_page, "dark", failure_details)
    
    @pytest.mark.asyncio
    async def test_generate_theme_failure_diagnostic_success(self, theme_manager, mock_page):
        """测试生成主题失败诊断信息成功"""
        failure_details = ["方法1失败", "方法2失败"]
        
        with patch.object(theme_manager, 'detect_current_theme', return_value="light"):
            mock_page.evaluate.side_effect = ["complete", False, True]  # page_ready, has_error, network_online
            
            diagnostic = await theme_manager._generate_theme_failure_diagnostic(mock_page, "dark", failure_details)
        
        assert diagnostic["target_theme"] == "dark"
        assert diagnostic["failure_count"] == 2
        assert diagnostic["page_url"] == "https://www.bing.com"
        assert diagnostic["page_title"] == "Bing"
        assert diagnostic["current_theme"] == "light"
        assert diagnostic["page_ready_state"] == "complete"
        assert diagnostic["is_bing_page"] is True
        assert diagnostic["page_has_error"] is False
        assert diagnostic["network_online"] is True
    
    @pytest.mark.asyncio
    async def test_generate_theme_failure_diagnostic_with_errors(self, theme_manager, mock_page):
        """测试生成诊断信息时发生错误"""
        failure_details = ["方法失败"]
        
        with patch.object(theme_manager, 'detect_current_theme', side_effect=Exception("检测失败")):
            mock_page.evaluate.side_effect = Exception("JS执行失败")
            mock_page.title.side_effect = Exception("获取标题失败")
            
            diagnostic = await theme_manager._generate_theme_failure_diagnostic(mock_page, "dark", failure_details)
        
        assert diagnostic["target_theme"] == "dark"
        assert diagnostic["current_theme"] == "检测失败: 检测失败"
        assert diagnostic["page_ready_state"] == "未知"
        assert diagnostic["page_title"] == "获取失败"  # 修正期望值
    
    def test_generate_failure_suggestions_bing_page(self, theme_manager):
        """测试为Bing页面生成失败建议"""
        diagnostic_info = {
            "is_bing_page": True,
            "page_ready_state": "complete",
            "network_online": True,
            "page_has_error": False,
            "current_theme": "light",
            "failure_count": 3
        }
        
        suggestions = theme_manager._generate_failure_suggestions(diagnostic_info, "dark")
        
        assert len(suggestions) > 0
        assert "当前主题为 light，可能需要手动设置为 dark" in suggestions
        assert "尝试刷新页面后重新设置主题" in suggestions
    
    def test_generate_failure_suggestions_non_bing_page(self, theme_manager):
        """测试为非Bing页面生成失败建议"""
        diagnostic_info = {
            "is_bing_page": False,
            "page_ready_state": "loading",
            "network_online": False,
            "page_has_error": True,
            "current_theme": "未知",
            "failure_count": 6
        }
        
        suggestions = theme_manager._generate_failure_suggestions(diagnostic_info, "dark")
        
        assert "确保当前页面是Bing搜索页面 (bing.com)" in suggestions
        assert "等待页面完全加载后再尝试设置主题" in suggestions
        assert "检查网络连接是否正常" in suggestions
        assert "页面可能存在错误，尝试刷新页面后重试" in suggestions
        # 修正期望的建议文本 - 当前主题为"未知"时会生成不同的建议
        assert any("当前主题为 未知" in suggestion for suggestion in suggestions)
        assert "考虑在配置中禁用主题管理 (bing_theme.enabled: false)" in suggestions
    
    @pytest.mark.asyncio
    async def test_save_failure_screenshot_success(self, theme_manager, mock_page):
        """测试保存失败截图成功"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('time.time', return_value=1234567890):
                mock_page.screenshot.return_value = None
                
                result = await theme_manager._save_failure_screenshot(mock_page, "dark")
        
        assert result is True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_page.screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_failure_screenshot_failure(self, theme_manager, mock_page):
        """测试保存失败截图失败"""
        mock_page.screenshot.side_effect = Exception("截图失败")
        
        result = await theme_manager._save_failure_screenshot(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_failure_screenshot_no_page(self, theme_manager):
        """测试没有页面对象时保存截图"""
        result = await theme_manager._save_failure_screenshot(None, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_theme_with_fallback_standard_success(self, theme_manager, mock_page):
        """测试带降级策略的主题设置 - 标准方法成功"""
        with patch.object(theme_manager, 'set_theme', return_value=True) as mock_set:
            result = await theme_manager.set_theme_with_fallback(mock_page, "dark")
        
        assert result is True
        mock_set.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_set_theme_with_fallback_force_success(self, theme_manager, mock_page):
        """测试带降级策略的主题设置 - 强制应用成功"""
        with patch.object(theme_manager, 'set_theme', return_value=False):
            with patch.object(theme_manager, 'force_theme_application', return_value=True) as mock_force:
                result = await theme_manager.set_theme_with_fallback(mock_page, "dark")
        
        assert result is True
        mock_force.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_set_theme_with_fallback_css_success(self, theme_manager, mock_page):
        """测试带降级策略的主题设置 - CSS应用成功"""
        with patch.object(theme_manager, 'set_theme', return_value=False):
            with patch.object(theme_manager, 'force_theme_application', return_value=False):
                with patch.object(theme_manager, '_apply_css_only_theme', return_value=True) as mock_css:
                    result = await theme_manager.set_theme_with_fallback(mock_page, "dark")
        
        assert result is True
        mock_css.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_set_theme_with_fallback_minimal_success(self, theme_manager, mock_page):
        """测试带降级策略的主题设置 - 最小化标记成功"""
        with patch.object(theme_manager, 'set_theme', return_value=False):
            with patch.object(theme_manager, 'force_theme_application', return_value=False):
                with patch.object(theme_manager, '_apply_css_only_theme', return_value=False):
                    with patch.object(theme_manager, '_apply_minimal_theme_markers', return_value=True) as mock_minimal:
                        result = await theme_manager.set_theme_with_fallback(mock_page, "dark")
        
        assert result is True
        mock_minimal.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_set_theme_with_fallback_all_fail(self, theme_manager, mock_page):
        """测试带降级策略的主题设置 - 所有方法都失败"""
        with patch.object(theme_manager, 'set_theme', return_value=False):
            with patch.object(theme_manager, 'force_theme_application', return_value=False):
                with patch.object(theme_manager, '_apply_css_only_theme', return_value=False):
                    with patch.object(theme_manager, '_apply_minimal_theme_markers', return_value=False):
                        result = await theme_manager.set_theme_with_fallback(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_apply_css_only_theme_success(self, theme_manager, mock_page):
        """测试仅CSS主题应用成功"""
        with patch.object(theme_manager, '_generate_force_theme_css', return_value="css content"):
            mock_page.add_style_tag.return_value = None
            mock_page.evaluate.return_value = None
            
            result = await theme_manager._apply_css_only_theme(mock_page, "dark")
        
        assert result is True
        mock_page.add_style_tag.assert_called_once_with(content="css content")
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_apply_css_only_theme_failure(self, theme_manager, mock_page):
        """测试仅CSS主题应用失败"""
        mock_page.add_style_tag.side_effect = Exception("CSS注入失败")
        
        result = await theme_manager._apply_css_only_theme(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_apply_minimal_theme_markers_success(self, theme_manager, mock_page):
        """测试最小化主题标记应用成功"""
        mock_page.evaluate.return_value = True
        
        result = await theme_manager._apply_minimal_theme_markers(mock_page, "dark")
        
        assert result is True
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_apply_minimal_theme_markers_failure(self, theme_manager, mock_page):
        """测试最小化主题标记应用失败"""
        mock_page.evaluate.side_effect = Exception("JS执行失败")
        
        result = await theme_manager._apply_minimal_theme_markers(mock_page, "dark")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_with_fallback(self, theme_manager, mock_page):
        """测试搜索前主题检查使用降级策略"""
        # 禁用持久化以简化测试
        theme_manager.persistence_enabled = False
        
        with patch.object(theme_manager, 'detect_current_theme', new_callable=AsyncMock, return_value="light"):
            with patch.object(theme_manager, 'set_theme', new_callable=AsyncMock, return_value=False):
                with patch.object(theme_manager, 'set_theme_with_fallback', new_callable=AsyncMock, return_value=True) as mock_fallback:
                    result = await theme_manager.ensure_theme_before_search(mock_page)
        
        assert result is True
        mock_fallback.assert_called_once_with(mock_page, "dark")
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_all_fail_continue(self, theme_manager, mock_page):
        """测试搜索前主题检查全部失败但继续搜索"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="light"):
            with patch.object(theme_manager, 'set_theme', return_value=False):
                with patch.object(theme_manager, 'set_theme_with_fallback', return_value=False):
                    result = await theme_manager.ensure_theme_before_search(mock_page)
        
        # 即使所有主题设置都失败，也应该返回True以继续搜索
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_failure_statistics(self, theme_manager):
        """测试获取失败统计信息"""
        stats = await theme_manager.get_failure_statistics()
        
        assert "config" in stats
        assert "last_check_time" in stats
        assert "available_methods" in stats
        assert "fallback_strategies" in stats
        
        assert len(stats["available_methods"]) == 6
        assert len(stats["fallback_strategies"]) == 3
        assert stats["config"]["enabled"] is True
        assert stats["config"]["preferred_theme"] == "dark"
    
    @pytest.mark.asyncio
    async def test_set_theme_enhanced_failure_handling(self, theme_manager, mock_page):
        """测试增强的主题设置失败处理"""
        # 模拟所有设置方法都失败
        with patch.object(theme_manager, 'detect_current_theme', return_value="light"):
            with patch.object(theme_manager, '_set_theme_by_url', return_value=False):
                with patch.object(theme_manager, '_set_theme_by_cookie', return_value=False):
                    with patch.object(theme_manager, '_set_theme_by_localstorage', return_value=False):
                        with patch.object(theme_manager, '_set_theme_by_javascript', return_value=False):
                            with patch.object(theme_manager, '_set_theme_by_settings', return_value=False):
                                with patch.object(theme_manager, '_set_theme_by_force_css', return_value=False):
                                    with patch.object(theme_manager, '_handle_theme_setting_failure') as mock_handle:
                                        result = await theme_manager.set_theme(mock_page, "dark")
        
        assert result is False
        mock_handle.assert_called_once()
        # 验证传递了失败详情
        call_args = mock_handle.call_args
        assert call_args[0][0] == mock_page  # page
        assert call_args[0][1] == "dark"     # theme
        assert len(call_args[0][2]) == 6     # failure_details 包含6个方法的失败信息


class TestBingThemeManagerVerification:
    """BingThemeManager主题设置验证测试类 - 任务6.2.1的测试"""
    
    @pytest.fixture
    def theme_manager(self):
        """创建主题管理器实例"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True
        }.get(key, default)
        return BingThemeManager(config)
    
    @pytest.fixture
    def mock_page(self):
        """模拟Playwright页面"""
        page = AsyncMock()
        page.url = "https://www.bing.com"
        page.context = AsyncMock()
        page.title.return_value = "Bing"
        page.evaluate.return_value = "Mozilla/5.0"
        return page
    
    @pytest.mark.asyncio
    async def test_verify_theme_setting_success(self, theme_manager, mock_page):
        """测试主题设置验证成功"""
        # 模拟所有检测方法都返回期望主题
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            with patch.object(theme_manager, '_verify_theme_by_all_methods') as mock_verify_methods:
                with patch.object(theme_manager, '_verify_theme_persistence_detailed') as mock_persistence:
                    
                    # 设置模拟返回值
                    mock_verify_methods.return_value = {
                        "css_classes": {"result": "dark", "matches_expected": True, "weight": 3, "status": "success"},
                        "computed_styles": {"result": "dark", "matches_expected": True, "weight": 3, "status": "success"},
                        "cookies": {"result": "dark", "matches_expected": True, "weight": 2, "status": "success"}
                    }
                    
                    mock_persistence.return_value = {
                        "is_persistent": True,
                        "before_refresh": "dark",
                        "after_refresh": "dark"
                    }
                    
                    result = await theme_manager.verify_theme_setting(mock_page, "dark")
        
        assert result["success"] is True
        assert result["expected_theme"] == "dark"
        assert result["detected_theme"] == "dark"
        assert result["persistence_check"] is True
        assert result["verification_score"] >= 0.7
        assert len(result["recommendations"]) > 0
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_verify_theme_setting_theme_mismatch(self, theme_manager, mock_page):
        """测试主题设置验证 - 主题不匹配"""
        # 模拟检测到不同的主题
        with patch.object(theme_manager, 'detect_current_theme', return_value="light"):
            with patch.object(theme_manager, '_verify_theme_by_all_methods') as mock_verify_methods:
                
                mock_verify_methods.return_value = {
                    "css_classes": {"result": "light", "matches_expected": False, "weight": 3, "status": "success"},
                    "computed_styles": {"result": "light", "matches_expected": False, "weight": 3, "status": "success"}
                }
                
                result = await theme_manager.verify_theme_setting(mock_page, "dark")
        
        assert result["success"] is False
        assert result["expected_theme"] == "dark"
        assert result["detected_theme"] == "light"
        assert result["persistence_check"] is False  # 跳过持久化验证
        assert "当前主题为 light，但期望为 dark" in " ".join(result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_verify_theme_setting_no_theme_detected(self, theme_manager, mock_page):
        """测试主题设置验证 - 无法检测主题"""
        with patch.object(theme_manager, 'detect_current_theme', return_value=None):
            result = await theme_manager.verify_theme_setting(mock_page, "dark")
        
        assert result["success"] is False
        assert result["expected_theme"] == "dark"
        assert result["detected_theme"] is None
        assert result["error"] == "无法检测当前主题"
        assert "页面可能未完全加载或不支持主题检测" in result["recommendations"]
    
    @pytest.mark.asyncio
    async def test_verify_theme_setting_low_score(self, theme_manager, mock_page):
        """测试主题设置验证 - 验证分数过低"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            with patch.object(theme_manager, '_verify_theme_by_all_methods') as mock_verify_methods:
                with patch.object(theme_manager, '_verify_theme_persistence_detailed') as mock_persistence:
                    
                    # 设置大部分方法失败的情况
                    mock_verify_methods.return_value = {
                        "css_classes": {"result": "dark", "matches_expected": True, "weight": 3, "status": "success"},
                        "computed_styles": {"result": "light", "matches_expected": False, "weight": 3, "status": "success"},
                        "cookies": {"result": None, "matches_expected": False, "weight": 2, "status": "error"},
                        "storage": {"result": "light", "matches_expected": False, "weight": 1, "status": "success"}
                    }
                    
                    mock_persistence.return_value = {"is_persistent": True}
                    
                    result = await theme_manager.verify_theme_setting(mock_page, "dark")
        
        assert result["success"] is False  # 分数过低导致失败
        assert result["verification_score"] < 0.7
        assert any("验证分数" in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_verify_theme_setting_exception(self, theme_manager, mock_page):
        """测试主题设置验证异常"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=Exception("检测异常")):
            result = await theme_manager.verify_theme_setting(mock_page, "dark")
        
        assert result["success"] is False
        assert "主题设置验证异常" in result["error"]
        assert "验证过程中发生异常" in " ".join(result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_verify_theme_by_all_methods_success(self, theme_manager, mock_page):
        """测试所有方法验证主题成功"""
        # 模拟各种检测方法
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', return_value="dark"):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="dark"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', return_value="dark"):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value=None):
                                
                                result = await theme_manager._verify_theme_by_all_methods(mock_page, "dark")
        
        assert len(result) == 6  # 6种检测方法
        assert result["css_classes"]["matches_expected"] is True
        assert result["computed_styles"]["matches_expected"] is True
        assert result["cookies"]["matches_expected"] is True
        assert result["url_params"]["matches_expected"] is False  # None != "dark"
        assert result["storage"]["matches_expected"] is True
        assert result["meta_tags"]["matches_expected"] is False  # None != "dark"
    
    @pytest.mark.asyncio
    async def test_verify_theme_by_all_methods_with_errors(self, theme_manager, mock_page):
        """测试验证方法中有错误的情况"""
        with patch.object(theme_manager, '_detect_theme_by_css_classes', return_value="dark"):
            with patch.object(theme_manager, '_detect_theme_by_computed_styles', side_effect=Exception("样式错误")):
                with patch.object(theme_manager, '_detect_theme_by_cookies', return_value="light"):
                    with patch.object(theme_manager, '_detect_theme_by_url_params', return_value=None):
                        with patch.object(theme_manager, '_detect_theme_by_storage', side_effect=Exception("存储错误")):
                            with patch.object(theme_manager, '_detect_theme_by_meta_tags', return_value="dark"):
                                
                                result = await theme_manager._verify_theme_by_all_methods(mock_page, "dark")
        
        assert result["css_classes"]["status"] == "success"
        assert result["computed_styles"]["status"] == "error"
        assert result["cookies"]["matches_expected"] is False  # "light" != "dark"
        assert result["storage"]["status"] == "error"
        assert result["meta_tags"]["matches_expected"] is True
    
    def test_calculate_verification_score_perfect(self, theme_manager):
        """测试计算验证分数 - 完美匹配"""
        methods_result = {
            "css_classes": {"matches_expected": True, "weight": 3},
            "computed_styles": {"matches_expected": True, "weight": 3},
            "cookies": {"matches_expected": True, "weight": 2}
        }
        
        score = theme_manager._calculate_verification_score(methods_result, "dark", "dark")
        
        assert score == 1.0  # 完美分数 + 主题匹配加分
    
    def test_calculate_verification_score_partial(self, theme_manager):
        """测试计算验证分数 - 部分匹配"""
        methods_result = {
            "css_classes": {"matches_expected": True, "weight": 3},   # 3分
            "computed_styles": {"matches_expected": False, "weight": 3}, # 0分
            "cookies": {"matches_expected": True, "weight": 2}       # 2分
        }
        # 总权重: 8, 匹配权重: 5, 基础分数: 5/8 = 0.625
        
        score = theme_manager._calculate_verification_score(methods_result, "dark", "dark")
        
        assert 0.8 <= score <= 0.85  # 0.625 + 0.2 (主题匹配加分)
    
    def test_calculate_verification_score_no_match(self, theme_manager):
        """测试计算验证分数 - 无匹配"""
        methods_result = {
            "css_classes": {"matches_expected": False, "weight": 3},
            "computed_styles": {"matches_expected": False, "weight": 3}
        }
        
        score = theme_manager._calculate_verification_score(methods_result, "light", "dark")
        
        assert score == 0.0  # 无匹配且主题不符
    
    def test_calculate_verification_score_empty(self, theme_manager):
        """测试计算验证分数 - 空结果"""
        score = theme_manager._calculate_verification_score({}, "dark", "dark")
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_detailed_success(self, theme_manager, mock_page):
        """测试详细持久化验证成功"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["dark", "dark"]):
            with patch.object(theme_manager, '_verify_theme_by_all_methods') as mock_verify:
                mock_verify.side_effect = [
                    {"css_classes": {"matches_expected": True}},  # 刷新前
                    {"css_classes": {"matches_expected": True}}   # 刷新后
                ]
                
                result = await theme_manager._verify_theme_persistence_detailed(mock_page, "dark")
        
        assert result["is_persistent"] is True
        assert result["before_refresh"] == "dark"
        assert result["after_refresh"] == "dark"
        assert result["refresh_successful"] is True
        assert result["error"] is None
        mock_page.reload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_detailed_failure(self, theme_manager, mock_page):
        """测试详细持久化验证失败"""
        with patch.object(theme_manager, 'detect_current_theme', side_effect=["dark", "light"]):
            with patch.object(theme_manager, '_verify_theme_by_all_methods') as mock_verify:
                mock_verify.side_effect = [
                    {"css_classes": {"matches_expected": True}},   # 刷新前
                    {"css_classes": {"matches_expected": False}}   # 刷新后
                ]
                
                result = await theme_manager._verify_theme_persistence_detailed(mock_page, "dark")
        
        assert result["is_persistent"] is False
        assert result["before_refresh"] == "dark"
        assert result["after_refresh"] == "light"
        assert result["refresh_successful"] is True
    
    @pytest.mark.asyncio
    async def test_verify_theme_persistence_detailed_refresh_failure(self, theme_manager, mock_page):
        """测试详细持久化验证 - 页面刷新失败"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            with patch.object(theme_manager, '_verify_theme_by_all_methods', return_value={}):
                mock_page.reload.side_effect = Exception("刷新失败")
                
                result = await theme_manager._verify_theme_persistence_detailed(mock_page, "dark")
        
        assert result["is_persistent"] is False
        assert result["refresh_successful"] is False
        assert "页面刷新失败" in result["error"]
    
    def test_generate_verification_recommendations_theme_mismatch(self, theme_manager):
        """测试生成验证建议 - 主题不匹配"""
        verification_result = {"verification_score": 0.8, "persistence_check": True}
        methods_result = {}
        
        recommendations = theme_manager._generate_verification_recommendations(
            verification_result, methods_result, "light", "dark"
        )
        
        assert any("当前主题为 light，但期望为 dark" in rec for rec in recommendations)
        assert any("可以尝试使用强制主题应用功能" in rec for rec in recommendations)
    
    def test_generate_verification_recommendations_no_theme(self, theme_manager):
        """测试生成验证建议 - 无法检测主题"""
        verification_result = {"verification_score": 0.0, "persistence_check": False}
        methods_result = {}
        
        recommendations = theme_manager._generate_verification_recommendations(
            verification_result, methods_result, None, "dark"
        )
        
        assert any("无法检测到当前主题" in rec for rec in recommendations)
        assert any("确保页面完全加载后再进行主题验证" in rec for rec in recommendations)
    
    def test_generate_verification_recommendations_low_score(self, theme_manager):
        """测试生成验证建议 - 低验证分数"""
        verification_result = {"verification_score": 0.2, "persistence_check": True}
        methods_result = {}
        
        recommendations = theme_manager._generate_verification_recommendations(
            verification_result, methods_result, "dark", "dark"
        )
        
        assert any("验证分数过低" in rec for rec in recommendations)
        assert any("可能需要使用多种主题设置方法" in rec for rec in recommendations)
    
    def test_generate_verification_recommendations_method_errors(self, theme_manager):
        """测试生成验证建议 - 方法错误"""
        verification_result = {"verification_score": 0.5, "persistence_check": True}
        methods_result = {
            "css_classes": {"status": "error", "matches_expected": False},
            "cookies": {"status": "success", "matches_expected": False}
        }
        
        recommendations = theme_manager._generate_verification_recommendations(
            verification_result, methods_result, "dark", "dark"
        )
        
        assert any("css_classes" in rec and "发生错误" in rec for rec in recommendations)
        assert any("cookies" in rec and "未匹配期望主题" in rec for rec in recommendations)
    
    def test_generate_verification_recommendations_success(self, theme_manager):
        """测试生成验证建议 - 完全成功"""
        verification_result = {"verification_score": 1.0, "persistence_check": True}
        methods_result = {}
        
        recommendations = theme_manager._generate_verification_recommendations(
            verification_result, methods_result, "dark", "dark"
        )
        
        assert any("主题验证完全成功" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_initial_success(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 初始验证成功"""
        mock_verification = {
            "success": True,
            "verification_score": 0.9,
            "detected_theme": "dark"
        }
        
        with patch.object(theme_manager, 'verify_theme_setting', return_value=mock_verification):
            result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark")
        
        assert result["final_success"] is True
        assert result["initial_verification"]["success"] is True
        assert result["total_attempts"] == 0  # 无需修复
        assert len(result["fix_attempts"]) == 0
        assert result["final_verification"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_fix_success_first_attempt(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 第一次修复成功"""
        initial_verification = {"success": False, "verification_score": 0.3}
        success_verification = {"success": True, "verification_score": 0.9}
        
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=[initial_verification, success_verification]):
            with patch.object(theme_manager, 'set_theme', return_value=True):
                result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=3)
        
        assert result["final_success"] is True
        assert result["total_attempts"] == 1
        assert len(result["fix_attempts"]) == 1
        assert result["fix_attempts"][0]["method_used"] == "standard_setting"
        assert result["fix_attempts"][0]["success"] is True
        assert result["final_verification"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_fix_success_second_attempt(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 第二次修复成功"""
        initial_verification = {"success": False, "verification_score": 0.3}
        failed_verification = {"success": False, "verification_score": 0.4}
        success_verification = {"success": True, "verification_score": 0.9}
        
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=[initial_verification, failed_verification, success_verification]):
            with patch.object(theme_manager, 'set_theme', return_value=False):  # 第一次修复失败
                with patch.object(theme_manager, 'set_theme_with_retry', return_value=True):  # 第二次修复成功
                    with patch.object(theme_manager, 'set_theme_with_fallback', return_value=True):  # 第三次修复成功
                        result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=3)
        
        assert result["final_success"] is True
        assert result["total_attempts"] == 3  # 修正：实际会尝试3次，因为第2次修复后验证失败
        assert len(result["fix_attempts"]) == 3
        assert result["fix_attempts"][0]["method_used"] == "standard_setting"
        assert result["fix_attempts"][0]["success"] is False
        assert result["fix_attempts"][1]["method_used"] == "retry_setting"
        assert result["fix_attempts"][1]["success"] is True
        assert result["fix_attempts"][1]["verification_after_fix"]["success"] is False  # 验证失败
        assert result["fix_attempts"][2]["method_used"] == "fallback_setting"
        assert result["fix_attempts"][2]["success"] is True
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_fix_success_fallback(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 降级策略成功"""
        initial_verification = {"success": False, "verification_score": 0.3}
        success_verification = {"success": True, "verification_score": 0.8}
        
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=[initial_verification, success_verification]):
            with patch.object(theme_manager, 'set_theme', return_value=False):
                with patch.object(theme_manager, 'set_theme_with_retry', return_value=False):
                    with patch.object(theme_manager, 'set_theme_with_fallback', return_value=True):
                        result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=3)
        
        assert result["final_success"] is True
        assert result["total_attempts"] == 3
        assert result["fix_attempts"][2]["method_used"] == "fallback_setting"
        assert result["fix_attempts"][2]["success"] is True
        assert result["fix_attempts"][2]["verification_after_fix"]["success"] is True  # 最终验证成功
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_fix_success_second_attempt_with_verification(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 第二次修复成功且验证通过"""
        initial_verification = {"success": False, "verification_score": 0.3}
        success_verification = {"success": True, "verification_score": 0.9}
        
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=[initial_verification, success_verification]):
            with patch.object(theme_manager, 'set_theme', return_value=False):  # 第一次修复失败
                with patch.object(theme_manager, 'set_theme_with_retry', return_value=True):  # 第二次修复成功
                    result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=3)
        
        assert result["final_success"] is True
        assert result["total_attempts"] == 2  # 第二次就成功了
        assert len(result["fix_attempts"]) == 2
        assert result["fix_attempts"][0]["method_used"] == "standard_setting"
        assert result["fix_attempts"][0]["success"] is False
        assert result["fix_attempts"][1]["method_used"] == "retry_setting"
        assert result["fix_attempts"][1]["success"] is True
        assert result["fix_attempts"][1]["verification_after_fix"]["success"] is True  # 验证成功
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_all_attempts_fail(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 所有尝试都失败"""
        failed_verification = {"success": False, "verification_score": 0.3}
        
        with patch.object(theme_manager, 'verify_theme_setting', return_value=failed_verification):
            with patch.object(theme_manager, 'set_theme', return_value=False):
                with patch.object(theme_manager, 'set_theme_with_retry', return_value=False):
                    with patch.object(theme_manager, 'set_theme_with_fallback', return_value=False):
                        result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=2)
        
        assert result["final_success"] is False
        assert result["total_attempts"] == 2
        assert len(result["fix_attempts"]) == 2
        assert all(attempt["success"] is False for attempt in result["fix_attempts"])
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_exception(self, theme_manager, mock_page):
        """测试验证和修复主题设置异常"""
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=Exception("验证异常")):
            result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark")
        
        assert result["final_success"] is False
        assert "验证和修复主题设置异常" in result["error"]
    
    @pytest.mark.asyncio
    async def test_verify_and_fix_theme_setting_fix_exception(self, theme_manager, mock_page):
        """测试验证和修复主题设置 - 修复过程异常"""
        initial_verification = {"success": False, "verification_score": 0.3}
        final_verification = {"success": False, "verification_score": 0.3}
        
        with patch.object(theme_manager, 'verify_theme_setting', side_effect=[initial_verification, final_verification]):
            with patch.object(theme_manager, 'set_theme', side_effect=Exception("设置异常")):
                result = await theme_manager.verify_and_fix_theme_setting(mock_page, "dark", max_attempts=1)
        
        assert result["final_success"] is False
        assert result["total_attempts"] == 1
        assert len(result["fix_attempts"]) == 1
        assert "设置异常" in result["fix_attempts"][0]["error"]


if __name__ == "__main__":
    pytest.main([__file__])