"""
ElementDetector 单元测试
测试元素检测器的多重选择器机制和页面状态检测
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser.element_detector import ElementDetector


class TestElementDetector:
    """ElementDetector 测试类"""

    @pytest.fixture
    def detector(self):
        """创建 ElementDetector 实例"""
        return ElementDetector()

    @pytest.fixture
    def mock_page(self):
        """创建模拟的 Playwright Page 对象"""
        page = Mock()
        page.wait_for_selector = AsyncMock()
        page.query_selector = AsyncMock()
        page.evaluate = AsyncMock()
        page.url = "https://www.bing.com"
        return page

    def test_init(self, detector):
        """测试初始化"""
        assert detector is not None
        assert len(detector.search_box_selectors) == 11
        assert "input[name='q']" in detector.search_box_selectors
        assert "input#sb_form_q" in detector.search_box_selectors

    @pytest.mark.asyncio
    async def test_find_search_box_success_first_selector(self, detector, mock_page):
        """测试搜索框检测 - 第一个选择器成功"""
        # 模拟第一个选择器找到元素
        mock_element = Mock()
        mock_element.is_visible = AsyncMock(return_value=True)
        mock_element.is_editable = AsyncMock(return_value=True)
        mock_element.evaluate = AsyncMock(return_value="input")
        mock_element.get_attribute = AsyncMock(return_value="text")
        mock_page.wait_for_selector.return_value = mock_element

        # Mock the validation method to return True
        with patch.object(detector, "_validate_search_box", return_value=True) as mock_validate:
            result = await detector.find_search_box(mock_page)

            assert result == mock_element
            # Check that wait_for_selector was called with the first selector
            mock_page.wait_for_selector.assert_called_once()
            call_args = mock_page.wait_for_selector.call_args
            assert call_args[0][0] == detector.search_box_selectors[0]
            assert call_args[1]["state"] == "visible"
            assert "timeout" in call_args[1]
            mock_validate.assert_called_once_with(mock_element)

    @pytest.mark.asyncio
    async def test_find_search_box_fallback_to_second_selector(self, detector, mock_page):
        """测试搜索框检测 - 降级到第二个选择器"""
        mock_element = Mock()
        mock_element.is_visible = AsyncMock(return_value=True)

        # 第一个选择器失败，第二个成功
        mock_page.wait_for_selector.side_effect = [Exception("First selector failed"), mock_element]

        # Mock the validation method to return True
        with patch.object(detector, "_validate_search_box", return_value=True) as mock_validate:
            result = await detector.find_search_box(mock_page)

            assert result == mock_element
            assert mock_page.wait_for_selector.call_count == 2
            mock_validate.assert_called_once_with(mock_element)

    @pytest.mark.asyncio
    async def test_find_search_box_all_selectors_fail(self, detector, mock_page):
        """测试搜索框检测 - 所有选择器都失败"""
        # 所有选择器都失败
        mock_page.wait_for_selector.side_effect = Exception("All selectors failed")

        result = await detector.find_search_box(mock_page)

        assert result is None
        assert mock_page.wait_for_selector.call_count == len(detector.search_box_selectors)

    @pytest.mark.asyncio
    async def test_find_search_box_element_not_visible(self, detector, mock_page):
        """测试搜索框检测 - 元素存在但不可见"""
        mock_element = Mock()
        mock_element.is_visible = AsyncMock(return_value=False)
        mock_page.wait_for_selector.return_value = mock_element

        # Mock the validation method to return False (element not valid)
        with patch.object(detector, "_validate_search_box", return_value=False):
            result = await detector.find_search_box(mock_page)

            assert result is None

    @pytest.mark.asyncio
    async def test_wait_for_page_ready_success(self, detector, mock_page):
        """测试页面准备就绪检测 - 成功"""
        # 模拟 wait_for_load_state 方法
        mock_page.wait_for_load_state = AsyncMock()

        result = await detector.wait_for_page_ready(mock_page, timeout=5000)

        assert result is True
        mock_page.wait_for_load_state.assert_called()

    @pytest.mark.asyncio
    async def test_wait_for_page_ready_with_network_check(self, detector, mock_page):
        """测试页面准备就绪检测 - 包含网络检查"""
        # 模拟 wait_for_load_state 方法
        mock_page.wait_for_load_state = AsyncMock()

        result = await detector.wait_for_page_ready(mock_page, timeout=5000, check_network=True)

        assert result is True
        assert mock_page.wait_for_load_state.call_count >= 1

    @pytest.mark.asyncio
    async def test_wait_for_page_ready_timeout(self, detector, mock_page):
        """测试页面准备就绪检测 - 超时"""
        # 模拟超时异常
        mock_page.wait_for_load_state = AsyncMock(side_effect=Exception("Timeout"))

        result = await detector.wait_for_page_ready(mock_page, timeout=100)

        assert result is False

    @pytest.mark.asyncio
    async def test_detect_page_errors_no_errors(self, detector, mock_page):
        """测试页面错误检测 - 无错误"""
        mock_page.title = AsyncMock(return_value="Bing Search")
        mock_page.url = "https://www.bing.com"
        mock_page.query_selector_all = AsyncMock(return_value=[])

        errors = await detector.detect_page_errors(mock_page)

        assert errors == []

    @pytest.mark.asyncio
    async def test_detect_page_errors_with_errors(self, detector, mock_page):
        """测试页面错误检测 - 有错误"""
        # 模拟页面标题包含错误
        mock_page.title = AsyncMock(return_value="404 Not Found")
        mock_page.url = "https://www.bing.com/error"
        mock_page.query_selector_all = AsyncMock(return_value=[])

        errors = await detector.detect_page_errors(mock_page)

        assert len(errors) >= 1
        assert any("404" in error or "error" in error.lower() for error in errors)

    @pytest.mark.asyncio
    async def test_take_diagnostic_screenshot(self, detector, mock_page):
        """测试诊断截图保存"""
        mock_page.screenshot = AsyncMock()

        with patch("os.makedirs") as mock_makedirs:
            result = await detector.take_diagnostic_screenshot(mock_page, "test_reason")

            mock_makedirs.assert_called_once()
            mock_page.screenshot.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_take_diagnostic_screenshot_failure(self, detector, mock_page):
        """测试诊断截图保存失败"""
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))

        # 不应该抛出异常
        result = await detector.take_diagnostic_screenshot(mock_page, "test_reason")
        assert result is False

    def test_get_element_info_available(self, detector):
        """测试获取元素信息"""
        # 测试基本属性存在
        assert hasattr(detector, "search_box_selectors")
        assert hasattr(detector, "search_button_selectors")
        assert hasattr(detector, "search_result_selectors")
        assert len(detector.search_box_selectors) > 0


@pytest.mark.asyncio
async def test_element_detector_integration():
    """集成测试 - 完整的元素检测流程"""
    detector = ElementDetector()

    # 创建更真实的模拟页面
    mock_page = Mock()
    mock_page.url = "https://www.bing.com"
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.title = AsyncMock(return_value="Bing Search")
    mock_page.query_selector_all = AsyncMock(return_value=[])

    # 模拟搜索框检测成功
    mock_element = Mock()
    mock_element.is_visible = AsyncMock(return_value=True)
    mock_element.is_editable = AsyncMock(return_value=True)
    mock_element.evaluate = AsyncMock(return_value="input")
    mock_element.get_attribute = AsyncMock(return_value="text")
    mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

    # 测试完整流程
    page_ready = await detector.wait_for_page_ready(mock_page)
    search_box = await detector.find_search_box(mock_page)
    errors = await detector.detect_page_errors(mock_page)

    assert page_ready is True
    assert search_box == mock_element
    assert errors == []


if __name__ == "__main__":
    pytest.main([__file__])
