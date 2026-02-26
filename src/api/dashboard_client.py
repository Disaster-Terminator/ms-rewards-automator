"""
Dashboard API Client

Fetches points data from Microsoft Rewards Dashboard API.
"""

import logging
import re
from typing import Any

from playwright.async_api import Page

from constants import API_ENDPOINTS, REWARDS_URLS

logger = logging.getLogger(__name__)


class DashboardClient:
    """Client for fetching data from Microsoft Rewards Dashboard API"""

    def __init__(self, page: Page):
        """
        Initialize Dashboard client

        Args:
            page: Playwright Page object
        """
        self.page = page
        self._cached_points: int | None = None
        base = REWARDS_URLS.get("dashboard", "https://rewards.bing.com")
        self._base_url = base.rstrip("/")

    async def get_current_points(self) -> int | None:
        """
        Get current points from Dashboard API

        Attempts to fetch points via API call first, falls back to
        parsing page content if API fails.

        Returns:
            Points balance or None if unable to determine
        """
        try:
            points = await self._fetch_points_via_api()
            if points is not None and points >= 0:
                self._cached_points = points
                return points
        except TimeoutError as e:
            logger.warning(f"API request timeout: {e}")
        except ConnectionError as e:
            logger.warning(f"API connection error: {e}")
        except Exception as e:
            logger.warning(f"API call failed: {e}")

        try:
            points = await self._fetch_points_via_page_content()
            if points is not None and points >= 0:
                self._cached_points = points
                return points
        except Exception as e:
            logger.debug(f"Page content parsing failed: {e}")

        return self._cached_points

    async def _fetch_points_via_api(self) -> int | None:
        """
        Fetch points via internal API endpoint

        Returns:
            Points balance or None
        """
        try:
            api_url = f"{self._base_url}{API_ENDPOINTS['dashboard_balance']}"
            response = await self.page.evaluate(
                f"""
                async () => {{
                    try {{
                        const resp = await fetch('{api_url}', {{
                            method: 'GET',
                            credentials: 'include'
                        }});
                        if (!resp.ok) return null;
                        return await resp.json();
                    }} catch {{
                        return null;
                    }}
                }}
                """
            )

            if response and isinstance(response, dict):
                available = response.get("availablePoints")
                balance = response.get("pointsBalance")
                points = available if available is not None else balance
                if points is not None:
                    try:
                        return int(points)
                    except (ValueError, TypeError):
                        pass

        except Exception as e:
            logger.debug(f"API fetch error: {e}")

        return None

    async def _fetch_points_via_page_content(self) -> int | None:
        """
        Extract points from page content as fallback

        Returns:
            Points balance or None
        """
        try:
            content = await self.page.content()

            patterns = [
                r'"availablePoints"\s*:\s*(\d+)',
                r'"pointsBalance"\s*:\s*(\d+)',
                r'"totalPoints"\s*:\s*(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    points = int(match.group(1))
                    if 0 <= points <= 1000000:
                        return points

        except Exception as e:
            logger.debug(f"Page content extraction error: {e}")

        return None

    async def get_dashboard_data(self) -> dict[str, Any] | None:
        """
        Fetch full dashboard data

        Returns:
            Dashboard data dict or None
        """
        try:
            api_url = f"{self._base_url}{API_ENDPOINTS['dashboard_data']}"
            response = await self.page.evaluate(
                f"""
                async () => {{
                    try {{
                        const resp = await fetch('{api_url}', {{
                            method: 'GET',
                            credentials: 'include'
                        }});
                        if (!resp.ok) return null;
                        return await resp.json();
                    }} catch {{
                        return null;
                    }}
                }}
                """
            )

            if response is not None and isinstance(response, dict):
                return dict(response)

        except TimeoutError as e:
            logger.warning(f"Dashboard API timeout: {e}")
        except ConnectionError as e:
            logger.warning(f"Dashboard API connection error: {e}")
        except Exception as e:
            logger.warning(f"Dashboard API error: {e}")

        return None
