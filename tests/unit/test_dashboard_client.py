"""Dashboard Client 单元测试"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import respx

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.dashboard_client import DashboardClient, DashboardError
from api.models import DashboardData, SearchCounters


@pytest.fixture
def mock_page():
    """Mock Playwright Page 对象"""
    page = Mock()
    page.context = Mock()

    async def mock_cookies(urls=None):
        return [
            {"name": "cookie1", "value": "value1", "domain": "rewards.bing.com"},
            {"name": "cookie2", "value": "value2", "domain": ".rewards.bing.com"},
        ]

    page.context.cookies = mock_cookies
    page.content = AsyncMock(
        return_value="""
        <html>
            <script>
                var dashboard = {
                    "userStatus": {
                        "availablePoints": 12345,
                        "levelInfo": {
                            "activeLevel": "newLevel3",
                            "activeLevelName": "Gold Member",
                            "progress": 1790,
                            "progressMax": 750
                        },
                        "counters": {
                            "pcSearch": [{
                                "progress": 15,
                                "maxProgress": 30
                            }],
                            "mobileSearch": [{
                                "progress": 10,
                                "maxProgress": 20
                            }]
                        }
                    }
                };
            </script>
        </html>
    """
    )
    return page


@pytest.fixture
def mock_page_no_dashboard():
    """没有 dashboard 变量的 Mock Page"""
    page = Mock()
    page.context = Mock()

    async def mock_cookies(urls=None):
        return [{"name": "cookie1", "value": "value1", "domain": "rewards.bing.com"}]

    page.context.cookies = mock_cookies
    page.content = AsyncMock(return_value="<html><body>no dashboard</body></html>")
    return page


@pytest.fixture
def mock_api_response():
    """Mock API 成功响应数据"""
    return {
        "dashboard": {
            "userStatus": {
                "availablePoints": 12345,
                "levelInfo": {
                    "activeLevel": "newLevel3",
                    "activeLevelName": "Gold Member",
                    "progress": 1790,
                    "progressMax": 750,
                },
                "counters": {
                    "pcSearch": [{"progress": 15, "maxProgress": 30}],
                    "mobileSearch": [{"progress": 10, "maxProgress": 20}],
                },
            },
            "dailySetPromotions": {},
            "morePromotions": [],
            "punchCards": [],
        }
    }


async def test_dashboard_data_from_dict():
    """测试 DashboardData.from_dict 方法"""
    data = {
        "userStatus": {
            "availablePoints": 12345,
            "levelInfo": {
                "activeLevel": "newLevel3",
                "activeLevelName": "Gold Member",
                "progress": 1790,
                "progressMax": 750,
            },
            "counters": {
                "pcSearch": [{"progress": 15, "maxProgress": 30}],
                "mobileSearch": [{"progress": 10, "maxProgress": 20}],
            },
        }
    }

    dashboard_data = DashboardData.from_dict(data)
    assert isinstance(dashboard_data, DashboardData)
    assert dashboard_data.user_status.available_points == 12345
    assert dashboard_data.user_status.level_info.active_level == "newLevel3"
    assert len(dashboard_data.user_status.counters.pc_search) == 1
    assert dashboard_data.user_status.counters.pc_search[0].progress == 15


async def test_dashboard_data_from_dict_missing_fields():
    """测试 DashboardData.from_dict 方法（缺失字段）"""
    data = {}

    dashboard_data = DashboardData.from_dict(data)
    assert isinstance(dashboard_data, DashboardData)
    assert dashboard_data.user_status.available_points == 0
    assert dashboard_data.user_status.level_info.active_level == ""
    assert len(dashboard_data.user_status.counters.pc_search) == 0


async def test_get_cookies_header(mock_page):
    """测试 _get_cookies_header 方法"""
    client = DashboardClient(mock_page)
    cookies = await client._get_cookies_header()
    assert "cookie1=value1" in cookies
    assert "cookie2=value2" in cookies


@respx.mock
async def test_get_dashboard_data_success(mock_page, mock_api_response):
    """测试 API 调用成功场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=mock_api_response
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_get_dashboard_data_api_error_fallback(mock_page):
    """测试 API 错误 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=500, text="Internal Server Error"
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_get_dashboard_data_unauthorized_fallback(mock_page):
    """测试 401 错误 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=401, text="Unauthorized"
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_get_dashboard_data_forbidden_fallback(mock_page):
    """测试 403 错误 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=403, text="Forbidden"
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_get_dashboard_data_html_fallback_fails(mock_page_no_dashboard):
    """测试 HTML fallback 失败场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=500, text="Internal Server Error"
    )

    client = DashboardClient(mock_page_no_dashboard)
    with pytest.raises(DashboardError):
        await client.get_dashboard_data()


@respx.mock
async def test_get_current_points(mock_page, mock_api_response):
    """测试 get_current_points 方法"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=mock_api_response
    )

    client = DashboardClient(mock_page)
    points = await client.get_current_points()
    assert points == 12345


@respx.mock
async def test_get_search_counters(mock_page, mock_api_response):
    """测试 get_search_counters 方法"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=mock_api_response
    )

    client = DashboardClient(mock_page)
    counters = await client.get_search_counters()
    assert isinstance(counters, SearchCounters)
    assert len(counters.pc_search) == 1
    assert len(counters.mobile_search) == 1
    assert counters.pc_search[0].progress == 15
    assert counters.mobile_search[0].progress == 10


@respx.mock
async def test_retry_logic(mock_page):
    """测试重试逻辑"""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(500, text="Internal Server Error")
        else:
            return httpx.Response(
                200, json={"dashboard": {"userStatus": {"availablePoints": 9999}}}
            )

    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").mock(side_effect=side_effect)

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert data.user_status.available_points == 9999
    assert call_count == 3


@respx.mock
async def test_timeout_fallback(mock_page):
    """测试超时 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_network_error_fallback(mock_page):
    """测试网络错误 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").mock(
        side_effect=httpx.ConnectError("Connection failed")
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


def test_dashboard_error_is_auth_error():
    """测试 DashboardError.is_auth_error 方法"""
    error_401 = DashboardError("Unauthorized", status_code=401)
    error_403 = DashboardError("Forbidden", status_code=403)
    error_500 = DashboardError("Server Error", status_code=500)
    error_no_code = DashboardError("Unknown error")

    assert error_401.is_auth_error() is True
    assert error_403.is_auth_error() is True
    assert error_500.is_auth_error() is False
    assert error_no_code.is_auth_error() is False


@respx.mock
async def test_json_parse_error_fallback(mock_page):
    """测试 JSON 解析错误 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, text="invalid json {{{"
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_response_not_dict_fallback(mock_page):
    """测试响应不是 dict + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=[1, 2, 3]
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_missing_dashboard_field_fallback(mock_page):
    """测试缺少 dashboard 字段 + HTML fallback 场景"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json={"otherField": "value"}
    )

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert data.user_status.available_points == 12345


@respx.mock
async def test_get_current_points_returns_none_on_error(mock_page_no_dashboard):
    """测试 get_current_points 失败返回 None"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=500, text="Internal Server Error"
    )

    client = DashboardClient(mock_page_no_dashboard)
    points = await client.get_current_points()
    assert points is None


@respx.mock
async def test_get_search_counters_returns_none_on_error(mock_page_no_dashboard):
    """测试 get_search_counters 失败返回 None"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=500, text="Internal Server Error"
    )

    client = DashboardClient(mock_page_no_dashboard)
    counters = await client.get_search_counters()
    assert counters is None


async def test_camel_to_snake_conversion():
    """测试 camelCase 到 snake_case 的转换"""
    data = {
        "userStatus": {
            "availablePoints": 9999,
            "bingStarMonthlyBonusProgress": 100,
            "bingStarMonthlyBonusMaximum": 500,
            "defaultSearchEngineMonthlyBonusState": "active",
        }
    }

    dashboard_data = DashboardData.from_dict(data)
    assert dashboard_data.user_status.available_points == 9999
    assert dashboard_data.user_status.bing_star_monthly_bonus_progress == 100
    assert dashboard_data.user_status.bing_star_monthly_bonus_maximum == 500
    assert dashboard_data.user_status.default_search_engine_monthly_bonus_state == "active"


async def test_extra_fields_ignored():
    """测试额外字段被忽略"""
    data = {
        "userStatus": {
            "availablePoints": 12345,
            "unknownField1": "value1",
            "unknownField2": 123,
        },
        "unknownTopLevel": "ignored",
    }

    dashboard_data = DashboardData.from_dict(data)
    assert dashboard_data.user_status.available_points == 12345
    assert not hasattr(dashboard_data.user_status, "unknownField1")
    assert not hasattr(dashboard_data, "unknownTopLevel")


def test_missing_api_endpoint_raises_error(mock_page):
    """测试缺少 API 端点配置时抛出 ValueError"""
    from unittest.mock import patch

    with patch("api.dashboard_client.API_ENDPOINTS", {}):
        with pytest.raises(ValueError, match="dashboard"):
            DashboardClient(mock_page)


def test_missing_api_params_raises_error(mock_page):
    """测试缺少 API 参数配置时抛出 ValueError"""
    from unittest.mock import patch

    with patch("api.dashboard_client.API_PARAMS", {}):
        with pytest.raises(ValueError, match="dashboard_type"):
            DashboardClient(mock_page)


@respx.mock
async def test_auth_error_no_retry(mock_page):
    """测试 401/403 错误不重试，立即触发 fallback"""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(401, text="Unauthorized")

    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").mock(side_effect=side_effect)

    client = DashboardClient(mock_page)
    data = await client.get_dashboard_data()
    assert isinstance(data, DashboardData)
    assert call_count == 1


@respx.mock
async def test_client_close(mock_page, mock_api_response):
    """测试客户端关闭方法"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=mock_api_response
    )

    client = DashboardClient(mock_page)
    await client.close()
    assert client._client is None


@respx.mock
async def test_client_context_manager(mock_page, mock_api_response):
    """测试客户端上下文管理器"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=200, json=mock_api_response
    )

    async with DashboardClient(mock_page) as client:
        data = await client.get_dashboard_data()
        assert isinstance(data, DashboardData)

    assert client._client is None


@pytest.mark.parametrize("status_code", (401, 403))
@respx.mock
async def test_get_dashboard_data_auth_error_with_failing_html_fallback(
    status_code,
    mock_page_no_dashboard,
):
    """
    当 API 返回认证错误 (401/403) 且 HTML fallback 也失败时，
    应该抛出 DashboardError。
    """
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=status_code, text="Unauthorized"
    )

    client = DashboardClient(mock_page_no_dashboard)
    with pytest.raises(DashboardError) as exc_info:
        await client.get_dashboard_data()

    assert exc_info.value.status_code == status_code
    assert exc_info.value.is_auth_error()


@respx.mock
async def test_get_current_points_api_error_html_fallback(mock_page):
    """API 5xx 时应从 HTML fallback 中获取当前积分"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").respond(
        status_code=500, text="Internal Server Error"
    )

    client = DashboardClient(mock_page)
    points = await client.get_current_points()
    assert points == 12345


@respx.mock
async def test_get_search_counters_timeout_html_fallback(mock_page):
    """API 超时时应从 HTML fallback 中构建搜索计数器"""
    respx.get("https://rewards.bing.com/api/getuserinfo?type=1").mock(
        side_effect=httpx.TimeoutException("Request timed out")
    )

    client = DashboardClient(mock_page)
    counters = await client.get_search_counters()

    assert counters is not None
    assert len(counters.pc_search) == 1
    assert len(counters.mobile_search) == 1
    assert counters.pc_search[0].progress == 15
    assert counters.mobile_search[0].progress == 10


async def test_search_counters_handles_null_values():
    """测试 SearchCounters 处理 null/非列表值"""
    data = {
        "pc_search": None,
        "mobile_search": "invalid",
    }

    counters = SearchCounters.from_dict(data)
    assert counters.pc_search == []
    assert counters.mobile_search == []


async def test_search_counters_handles_scalar_values():
    """测试 SearchCounters 处理标量值"""
    data = {
        "pc_search": 123,
        "mobile_search": "string",
    }

    counters = SearchCounters.from_dict(data)
    assert counters.pc_search == []
    assert counters.mobile_search == []


async def test_cookie_filtering_by_domain(mock_page):
    """测试 Cookie 使用 Playwright URL 作用域选择"""

    async def mock_cookies(urls=None):
        return [
            {"name": "bing_cookie", "value": "bing_value", "domain": "bing.com"},
            {"name": "rewards_cookie", "value": "rewards_value", "domain": "rewards.bing.com"},
            {"name": "rewards_sub_cookie", "value": "sub_value", "domain": ".rewards.bing.com"},
        ]

    mock_page.context.cookies = mock_cookies

    client = DashboardClient(mock_page)
    cookies = await client._get_cookies_header()

    assert "bing_cookie=bing_value" in cookies
    assert "rewards_cookie=rewards_value" in cookies
    assert "rewards_sub_cookie=sub_value" in cookies
