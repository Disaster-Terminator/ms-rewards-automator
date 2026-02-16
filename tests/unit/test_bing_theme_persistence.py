"""
Bing主题持久化功能测试
测试任务6.2.2：添加会话间主题保持
"""

import asyncio
import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.bing_theme_manager import BingThemeManager


class TestBingThemePersistence:
    """Bing主题持久化测试类"""
    
    @pytest.fixture
    def temp_theme_file(self):
        """创建临时主题状态文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def mock_config(self, temp_theme_file):
        """模拟配置"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True,
            "bing_theme.persistence_enabled": True,
            "bing_theme.theme_state_file": temp_theme_file
        }.get(key, default)
        return config
    
    @pytest.fixture
    def theme_manager(self, mock_config):
        """创建主题管理器实例"""
        return BingThemeManager(mock_config)
    
    @pytest.fixture
    def mock_page(self):
        """模拟页面对象"""
        page = AsyncMock()
        page.url = "https://www.bing.com"
        page.title.return_value = "Bing"
        page.evaluate.return_value = True
        page.context = AsyncMock()
        return page
    
    @pytest.fixture
    def mock_context(self):
        """模拟浏览器上下文"""
        context = AsyncMock()
        context.storage_state.return_value = {
            "origins": [
                {
                    "origin": "https://www.bing.com",
                    "localStorage": []
                }
            ]
        }
        return context
    
    @pytest.mark.asyncio
    async def test_save_theme_state(self, theme_manager, temp_theme_file):
        """测试保存主题状态"""
        # 准备测试数据
        theme = "dark"
        context_info = {
            "user_agent": "test-agent",
            "viewport": {"width": 1280, "height": 720}
        }
        
        # 执行保存
        result = await theme_manager.save_theme_state(theme, context_info)
        
        # 验证结果
        assert result is True
        assert os.path.exists(temp_theme_file)
        
        # 验证文件内容
        with open(temp_theme_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["theme"] == theme
        assert saved_data["preferred_theme"] == "dark"
        assert saved_data["context_info"] == context_info
        assert "timestamp" in saved_data
        assert saved_data["version"] == "1.0"
    
    @pytest.mark.asyncio
    async def test_load_theme_state(self, theme_manager, temp_theme_file):
        """测试加载主题状态"""
        import time
        test_data = {
            "theme": "dark",
            "timestamp": time.time(),
            "preferred_theme": "dark",
            "force_theme": True,
            "context_info": {"test": "data"},
            "version": "1.0"
        }
        
        # 写入测试数据
        with open(temp_theme_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 执行加载
        result = await theme_manager.load_theme_state()
        
        # 验证结果
        assert result is not None
        assert result["theme"] == "dark"
        assert result["context_info"]["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_load_theme_state_file_not_exists(self, theme_manager):
        """测试加载不存在的主题状态文件"""
        result = await theme_manager.load_theme_state()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_load_theme_state_invalid_data(self, theme_manager, temp_theme_file):
        """测试加载无效的主题状态数据"""
        # 写入无效数据
        with open(temp_theme_file, 'w', encoding='utf-8') as f:
            json.dump({"invalid": "data"}, f)
        
        result = await theme_manager.load_theme_state()
        assert result is None
    
    def test_validate_theme_state_valid(self, theme_manager):
        """测试验证有效的主题状态数据"""
        import time
        valid_data = {
            "theme": "dark",
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        result = theme_manager._validate_theme_state(valid_data)
        assert result is True
    
    def test_validate_theme_state_missing_fields(self, theme_manager):
        """测试验证缺少字段的主题状态数据"""
        invalid_data = {
            "theme": "dark"
            # 缺少timestamp和version
        }
        
        result = theme_manager._validate_theme_state(invalid_data)
        assert result is False
    
    def test_validate_theme_state_invalid_theme(self, theme_manager):
        """测试验证无效主题值的数据"""
        import time
        invalid_data = {
            "theme": "invalid_theme",
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        result = theme_manager._validate_theme_state(invalid_data)
        assert result is False
    
    def test_validate_theme_state_expired(self, theme_manager):
        """测试验证过期的主题状态数据"""
        import time
        expired_data = {
            "theme": "dark",
            "timestamp": time.time() - (31 * 24 * 3600),  # 31天前
            "version": "1.0"
        }
        
        result = theme_manager._validate_theme_state(expired_data)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_restore_theme_from_state_success(self, theme_manager, mock_page, temp_theme_file):
        """测试成功从状态恢复主题"""
        import time
        test_data = {
            "theme": "dark",
            "timestamp": time.time(),
            "preferred_theme": "dark",
            "force_theme": True,
            "context_info": {},
            "version": "1.0"
        }
        
        with open(temp_theme_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 模拟当前主题检测和设置
        # 第一次调用返回"light"（需要恢复），第二次调用返回"dark"（验证成功）
        detect_calls = ["light", "dark"]
        with patch.object(theme_manager, 'detect_current_theme', side_effect=detect_calls), \
             patch.object(theme_manager, 'set_theme', return_value=True):
            
            result = await theme_manager.restore_theme_from_state(mock_page)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_restore_theme_from_state_no_saved_state(self, theme_manager, mock_page):
        """测试没有保存状态时的恢复"""
        result = await theme_manager.restore_theme_from_state(mock_page)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_restore_theme_from_state_already_correct(self, theme_manager, mock_page, temp_theme_file):
        """测试当前主题已经正确时的恢复"""
        import time
        test_data = {
            "theme": "dark",
            "timestamp": time.time(),
            "preferred_theme": "dark",
            "force_theme": True,
            "context_info": {},
            "version": "1.0"
        }
        
        with open(temp_theme_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 模拟当前主题已经正确
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager.restore_theme_from_state(mock_page)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_persistence(self, theme_manager, mock_page, mock_context):
        """测试确保主题持久化"""
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"), \
             patch.object(theme_manager, 'save_theme_state', return_value=True), \
             patch.object(theme_manager, '_set_browser_persistence_markers', return_value=True), \
             patch.object(theme_manager, '_save_theme_to_storage_state', return_value=True):
            
            result = await theme_manager.ensure_theme_persistence(mock_page, mock_context)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_persistence_disabled(self, mock_config, mock_page):
        """测试持久化禁用时的行为"""
        mock_config.get.side_effect = lambda key, default=None: {
            "bing_theme.enabled": True,
            "bing_theme.theme": "dark",
            "bing_theme.force_theme": True,
            "bing_theme.persistence_enabled": False,  # 禁用持久化
            "bing_theme.theme_state_file": "theme_state.json"
        }.get(key, default)
        
        theme_manager = BingThemeManager(mock_config)
        result = await theme_manager.ensure_theme_persistence(mock_page)
        assert result is True  # 禁用时应该返回True
    
    @pytest.mark.asyncio
    async def test_set_browser_persistence_markers(self, theme_manager, mock_page):
        """测试设置浏览器持久化标记"""
        mock_page.evaluate.return_value = True
        
        result = await theme_manager._set_browser_persistence_markers(mock_page, "dark")
        assert result is True
        
        # 验证JavaScript被调用
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_theme_to_storage_state(self, theme_manager, mock_context):
        """测试保存主题到存储状态"""
        result = await theme_manager._save_theme_to_storage_state(mock_context, "dark")
        assert result is True
        
        # 验证storage_state被调用
        mock_context.storage_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_theme_persistence_integrity(self, theme_manager, mock_page, temp_theme_file):
        """测试检查主题持久化完整性"""
        import time
        test_data = {
            "theme": "dark",
            "timestamp": time.time(),
            "preferred_theme": "dark",
            "force_theme": True,
            "context_info": {},
            "version": "1.0"
        }
        
        with open(temp_theme_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 模拟浏览器持久化检查
        mock_page.evaluate.return_value = {
            "localStorage_markers": {"theme_preference": "dark"},
            "sessionStorage_markers": {"current_theme": "dark"},
            "dom_markers": {"html_persistent_theme": "dark"}
        }
        
        with patch.object(theme_manager, 'detect_current_theme', return_value="dark"):
            result = await theme_manager.check_theme_persistence_integrity(mock_page)
        
        assert result["overall_status"] in ["good", "warning", "error"]
        assert "file_persistence" in result
        assert "browser_persistence" in result
        assert "theme_consistency" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_cleanup_theme_persistence(self, theme_manager, temp_theme_file):
        """测试清理主题持久化数据"""
        import time
        # 创建测试文件
        with open(temp_theme_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # 设置缓存
        theme_manager._theme_state_cache = {"test": "cache"}
        theme_manager._last_cache_update = time.time()
        
        result = await theme_manager.cleanup_theme_persistence()
        assert result is True
        
        # 验证文件被删除
        assert not os.path.exists(temp_theme_file)
        
        # 验证缓存被清理
        assert theme_manager._theme_state_cache is None
        assert theme_manager._last_cache_update == 0
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_with_persistence(self, theme_manager, mock_page, mock_context):
        """测试搜索前确保主题设置（包含持久化）"""
        with patch.object(theme_manager, 'restore_theme_from_state', return_value=True), \
             patch.object(theme_manager, 'ensure_theme_persistence', return_value=True):
            
            result = await theme_manager.ensure_theme_before_search(mock_page, mock_context)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_theme_before_search_restore_failed(self, theme_manager, mock_page, mock_context):
        """测试恢复失败时的搜索前主题确保"""
        with patch.object(theme_manager, 'restore_theme_from_state', return_value=False), \
             patch.object(theme_manager, 'detect_current_theme', return_value="light"), \
             patch.object(theme_manager, 'set_theme', return_value=True), \
             patch.object(theme_manager, 'ensure_theme_persistence', return_value=True):
            
            result = await theme_manager.ensure_theme_before_search(mock_page, mock_context)
            assert result is True


class TestThemePersistenceIntegration:
    """主题持久化集成测试"""
    
    @pytest.mark.asyncio
    async def test_theme_persistence_workflow(self):
        """测试完整的主题持久化工作流程"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # 创建配置
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "bing_theme.enabled": True,
                "bing_theme.theme": "dark",
                "bing_theme.force_theme": True,
                "bing_theme.persistence_enabled": True,
                "bing_theme.theme_state_file": temp_file
            }.get(key, default)
            
            # 创建主题管理器
            theme_manager = BingThemeManager(config)
            
            # 模拟页面和上下文
            mock_page = AsyncMock()
            mock_page.url = "https://www.bing.com"
            mock_context = AsyncMock()
            mock_context.storage_state.return_value = {"origins": []}
            
            # 1. 保存主题状态
            save_result = await theme_manager.save_theme_state("dark", {"test": "context"})
            assert save_result is True
            
            # 2. 验证文件存在
            assert os.path.exists(temp_file)
            
            # 3. 加载主题状态
            loaded_state = await theme_manager.load_theme_state()
            assert loaded_state is not None
            assert loaded_state["theme"] == "dark"
            
            # 4. 模拟恢复主题
            # 第一次调用返回"light"（需要恢复），第二次调用返回"dark"（验证成功）
            detect_calls = ["light", "dark"]
            with patch.object(theme_manager, 'detect_current_theme', side_effect=detect_calls), \
                 patch.object(theme_manager, 'set_theme', return_value=True):
                
                restore_result = await theme_manager.restore_theme_from_state(mock_page)
                assert restore_result is True
            
            # 5. 确保持久化
            # 模拟页面evaluate调用以避免序列化AsyncMock
            mock_page.evaluate.return_value = "test-user-agent"
            mock_page.viewport_size = {"width": 1280, "height": 720}
            
            with patch.object(theme_manager, 'detect_current_theme', return_value="dark"), \
                 patch.object(theme_manager, '_set_browser_persistence_markers', return_value=True), \
                 patch.object(theme_manager, '_save_theme_to_storage_state', return_value=True):
                
                persistence_result = await theme_manager.ensure_theme_persistence(mock_page, mock_context)
                assert persistence_result is True
            
            # 6. 清理
            cleanup_result = await theme_manager.cleanup_theme_persistence()
            assert cleanup_result is True
            assert not os.path.exists(temp_file)
            
        finally:
            # 确保清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])