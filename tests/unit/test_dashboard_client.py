"""
Tests for DashboardClient
"""

from unittest.mock import AsyncMock

import pytest


class TestDashboardClient:
    """Test DashboardClient functionality"""

    @pytest.fixture
    def mock_page(self):
        """Create mock page"""
        return AsyncMock()

    @pytest.fixture
    def dashboard_client(self, mock_page):
        """Create DashboardClient instance"""
        from api.dashboard_client import DashboardClient

        return DashboardClient(mock_page)

    def test_initialization(self, dashboard_client, mock_page):
        """Test DashboardClient initializes correctly"""
        assert dashboard_client.page is mock_page
        assert dashboard_client._cached_points is None

    @pytest.mark.asyncio
    async def test_get_current_points_api_success(self, dashboard_client, mock_page):
        """Test get_current_points returns points via API"""
        mock_page.evaluate = AsyncMock(return_value={"availablePoints": 5000})

        result = await dashboard_client.get_current_points()
        assert result == 5000

    @pytest.mark.asyncio
    async def test_get_current_points_api_returns_points_balance(self, dashboard_client, mock_page):
        """Test get_current_points uses pointsBalance field"""
        mock_page.evaluate = AsyncMock(return_value={"pointsBalance": 3000})

        result = await dashboard_client.get_current_points()
        assert result == 3000

    @pytest.mark.asyncio
    async def test_get_current_points_api_failure_fallback(self, dashboard_client, mock_page):
        """Test get_current_points falls back to page content on API failure"""
        mock_page.evaluate = AsyncMock(side_effect=[None, '{"availablePoints": 2500}'])
        mock_page.content = AsyncMock(return_value='{"availablePoints": 2500}')

        result = await dashboard_client.get_current_points()
        assert result == 2500

    @pytest.mark.asyncio
    async def test_get_current_points_timeout_error(self, dashboard_client, mock_page):
        """Test get_current_points handles timeout error"""
        mock_page.evaluate = AsyncMock(side_effect=TimeoutError("Request timeout"))
        mock_page.content = AsyncMock(return_value='{"availablePoints": 1000}')

        result = await dashboard_client.get_current_points()
        assert result == 1000

    @pytest.mark.asyncio
    async def test_get_current_points_connection_error(self, dashboard_client, mock_page):
        """Test get_current_points handles connection error"""
        mock_page.evaluate = AsyncMock(side_effect=ConnectionError("Connection failed"))
        mock_page.content = AsyncMock(return_value='{"availablePoints": 1000}')

        result = await dashboard_client.get_current_points()
        assert result == 1000

    @pytest.mark.asyncio
    async def test_get_current_points_returns_cached_on_failure(self, dashboard_client, mock_page):
        """Test get_current_points returns cached value on complete failure"""
        dashboard_client._cached_points = 8000
        mock_page.evaluate = AsyncMock(side_effect=Exception("Error"))
        mock_page.content = AsyncMock(side_effect=Exception("Error"))

        result = await dashboard_client.get_current_points()
        assert result == 8000

    @pytest.mark.asyncio
    async def test_get_current_points_returns_none_on_no_data(self, dashboard_client, mock_page):
        """Test get_current_points returns None when no data available"""
        mock_page.evaluate = AsyncMock(return_value=None)
        mock_page.content = AsyncMock(return_value="")

        result = await dashboard_client.get_current_points()
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_points_via_api_string_value(self, dashboard_client, mock_page):
        """Test _fetch_points_via_api handles string points value"""
        mock_page.evaluate = AsyncMock(return_value={"availablePoints": "7500"})

        result = await dashboard_client._fetch_points_via_api()
        assert result == 7500

    @pytest.mark.asyncio
    async def test_fetch_points_via_page_content(self, dashboard_client, mock_page):
        """Test _fetch_points_via_page_content extracts points"""
        mock_page.content = AsyncMock(return_value='{"pointsBalance": 6000}')

        result = await dashboard_client._fetch_points_via_page_content()
        assert result == 6000

    @pytest.mark.asyncio
    async def test_fetch_points_via_page_content_invalid_range(self, dashboard_client, mock_page):
        """Test _fetch_points_via_page_content rejects invalid range"""
        mock_page.content = AsyncMock(return_value='{"availablePoints": 99999999}')

        result = await dashboard_client._fetch_points_via_page_content()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_dashboard_data_success(self, dashboard_client, mock_page):
        """Test get_dashboard_data returns data"""
        mock_data = {"user": "test", "points": 1000}
        mock_page.evaluate = AsyncMock(return_value=mock_data)

        result = await dashboard_client.get_dashboard_data()
        assert result == mock_data

    @pytest.mark.asyncio
    async def test_get_dashboard_data_timeout(self, dashboard_client, mock_page):
        """Test get_dashboard_data handles timeout"""
        mock_page.evaluate = AsyncMock(side_effect=TimeoutError("Timeout"))

        result = await dashboard_client.get_dashboard_data()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_dashboard_data_connection_error(self, dashboard_client, mock_page):
        """Test get_dashboard_data handles connection error"""
        mock_page.evaluate = AsyncMock(side_effect=ConnectionError("Connection failed"))

        result = await dashboard_client.get_dashboard_data()
        assert result is None
