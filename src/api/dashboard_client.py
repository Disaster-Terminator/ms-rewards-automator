"""Dashboard API 客户端"""

import asyncio
import json
import logging
import re

import httpx
from playwright.async_api import Page

from constants import API_ENDPOINTS, API_PARAMS, REWARDS_URLS

from .models import DashboardData, SearchCounters

logger = logging.getLogger(__name__)


class DashboardError(Exception):
    """Dashboard API 错误"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    def is_auth_error(self) -> bool:
        """检查是否为认证错误 (401/403)"""
        return self.status_code in (401, 403)


class DashboardClient:
    """Dashboard API 客户端"""

    DEFAULT_MAX_RETRIES = 2
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 10.0

    def __init__(
        self,
        page: Page,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        timeout: float | None = None,
    ):
        """
        初始化 DashboardClient

        Args:
            page: Playwright Page 对象
            max_retries: 最大重试次数，默认 2
            retry_delay: 重试间隔（秒），默认 1.0
            timeout: 请求超时（秒），默认 10.0

        Raises:
            ValueError: 缺少必要的 API 端点配置
        """
        self._page = page
        self._max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self._retry_delay = retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

        if "dashboard" not in API_ENDPOINTS:
            raise ValueError("Missing 'dashboard' endpoint in API_ENDPOINTS")
        if "dashboard_type" not in API_PARAMS:
            raise ValueError("Missing 'dashboard_type' in API_PARAMS")

        base_url = API_ENDPOINTS["dashboard"]
        if not base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid API endpoint URL: {base_url}")

        query_param = API_PARAMS["dashboard_type"]
        if not query_param.startswith("?"):
            raise ValueError(f"Invalid API query parameter: {query_param}")

        self._api_url = base_url + query_param
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
            ),
        )

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _get_cookies_header(self) -> str:
        """
        从 Page context 获取 cookies 字符串

        使用 Playwright 的 URL 作用域 cookie 选择，让 Playwright 按浏览器规则
        返回对该 URL 生效的 cookies（包括父域 cookies）。

        Returns:
            cookies 字符串
        """
        cookies = await self._page.context.cookies([self._api_url])
        return "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    async def _call_api(self) -> DashboardData:
        """
        调用 Dashboard API

        Returns:
            DashboardData 对象

        Raises:
            DashboardError: API 调用失败
        """
        headers = {
            "Referer": REWARDS_URLS["dashboard"],
            "Cookie": await self._get_cookies_header(),
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        for attempt in range(self._max_retries + 1):
            try:
                if self._client is None or self._client.is_closed:
                    raise DashboardError("HTTP client has been closed")
                response = await self._client.get(self._api_url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict):
                    raise DashboardError(
                        f"Invalid API response from {self._api_url}: not a dict (attempt {attempt + 1})"
                    )
                if "dashboard" not in data:
                    raise DashboardError(
                        f"Invalid API response from {self._api_url}: missing 'dashboard' field (attempt {attempt + 1})"
                    )
                if not isinstance(data["dashboard"], dict):
                    raise DashboardError(
                        f"Invalid API response from {self._api_url}: 'dashboard' is not a dict (attempt {attempt + 1})"
                    )

                return self._parse_dashboard(data["dashboard"])

            except httpx.HTTPStatusError as e:
                raise DashboardError(
                    f"HTTP error {e.response.status_code} from {self._api_url}",
                    status_code=e.response.status_code,
                ) from e
            except httpx.TimeoutException as e:
                if attempt < self._max_retries:
                    logger.debug(
                        f"Request timeout, retrying ({attempt + 1}/{self._max_retries})..."
                    )
                    await asyncio.sleep(self._retry_delay)
                    continue
                raise DashboardError(
                    f"API timeout after {attempt + 1} attempts: {self._api_url}"
                ) from e
            except httpx.RequestError as e:
                if attempt < self._max_retries:
                    logger.debug(
                        f"Network error, retrying ({attempt + 1}/{self._max_retries}): {e}"
                    )
                    await asyncio.sleep(self._retry_delay)
                    continue
                raise DashboardError(
                    f"Network error after {attempt + 1} attempts: {self._api_url} - {e}"
                ) from e
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                raise DashboardError(f"Parse error from {self._api_url}: {e}") from e

    def _parse_dashboard(self, data: dict[str, object]) -> DashboardData:
        """
        解析 dashboard 数据

        Args:
            data: dashboard 数据字典

        Returns:
            DashboardData 对象
        """
        return DashboardData.from_dict(data)

    async def _html_fallback(self) -> DashboardData | None:
        """
        HTML fallback，从页面源码提取 dashboard 数据

        Returns:
            DashboardData 对象，失败返回 None
        """
        try:
            html = await self._page.content()
            match = re.search(r"var\s+dashboard\s*=\s*({.*?});", html, re.DOTALL)

            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return self._parse_dashboard(data)

            logger.warning("HTML fallback: dashboard variable not found in page")
            return None

        except json.JSONDecodeError as e:
            logger.warning(f"HTML fallback JSON parse error: {e}")
            return None
        except re.error as e:
            logger.warning(f"HTML fallback regex error: {e}")
            return None
        except (TypeError, KeyError, ValueError) as e:
            logger.warning(f"HTML fallback data parse error: {e}")
            return None

    async def get_dashboard_data(self) -> DashboardData:
        """
        获取完整 Dashboard 数据

        Returns:
            DashboardData 对象

        Raises:
            DashboardError: 所有数据源都失败
        """
        for attempt in range(self._max_retries + 1):
            try:
                return await self._call_api()
            except DashboardError as e:
                if e.is_auth_error():
                    logger.warning(f"Auth error ({e.status_code}), attempting HTML fallback")
                    fallback_data = await self._html_fallback()
                    if fallback_data:
                        return fallback_data
                    raise

                if e.status_code and 500 <= e.status_code < 600 and attempt < self._max_retries:
                    logger.warning(
                        f"Server error ({e.status_code}), attempt {attempt + 1} failed, retrying..."
                    )
                    await asyncio.sleep(self._retry_delay)
                    continue

                logger.warning("All API attempts failed, attempting HTML fallback")
                fallback_data = await self._html_fallback()
                if fallback_data:
                    return fallback_data
                raise

        raise DashboardError("Failed to get dashboard data")

    async def get_current_points(self) -> int | None:
        """
        获取当前积分

        Returns:
            当前积分，失败返回 None
        """
        try:
            data = await self.get_dashboard_data()
            return data.user_status.available_points
        except DashboardError as e:
            logger.warning(f"get_current_points failed: {e}")
            return None

    async def get_search_counters(self) -> SearchCounters | None:
        """
        获取搜索计数器

        Returns:
            SearchCounters 对象，失败返回 None
        """
        try:
            data = await self.get_dashboard_data()
            return data.user_status.counters
        except DashboardError as e:
            logger.warning(f"get_search_counters failed: {e}")
            return None
