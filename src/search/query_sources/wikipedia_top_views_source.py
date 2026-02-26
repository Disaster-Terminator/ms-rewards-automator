"""
Wikipedia Top Views query source - fetches trending topics from Wikipedia Pageviews API
"""

import time
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from constants import QUERY_SOURCE_URLS

from .query_source import QuerySource


class WikipediaTopViewsSource(QuerySource):
    """Query source that fetches trending topics from Wikipedia Pageviews API"""

    EXCLUDED_PREFIXES = [
        "Main_Page",
        "Special:",
        "File:",
        "Wikipedia:",
        "Template:",
        "Help:",
        "Category:",
        "Portal:",
        "Talk:",
        "User:",
        "Draft:",
        "List_of_",
    ]

    def __init__(self, config):
        """
        Initialize Wikipedia Top Views source

        Args:
            config: ConfigManager instance
        """
        super().__init__(config)
        self.timeout = config.get("query_engine.sources.wikipedia_top_views.timeout", 30)
        lang = config.get("query_engine.sources.wikipedia_top_views.lang", "en")
        if not isinstance(lang, str) or not lang.isalpha() or len(lang) > 10:
            self.logger.warning(f"Invalid lang '{lang}', using 'en'")
            self.lang = "en"
        else:
            self.lang = lang
        self.cache_ttl = config.get("query_engine.sources.wikipedia_top_views.ttl", 6 * 3600)
        self._available: bool = True
        self._session: aiohttp.ClientSession | None = None

        self._cache_data: list[str] | None = None
        self._cache_time: float = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        self.logger.info("WikipediaTopViewsSource initialized")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    def get_source_name(self) -> str:
        """Return the name of this source"""
        return "wikipedia_top_views"

    def get_priority(self) -> int:
        """Return priority (lower = higher priority)"""
        return 120

    def is_available(self) -> bool:
        """Check if this source is available"""
        return self._available

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total = self._cache_hits + self._cache_misses
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": self._cache_hits / total if total > 0 else 0,
        }

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid"""
        if self._cache_data is None:
            return False
        return bool(time.monotonic() - self._cache_time < self.cache_ttl)

    def _get_from_cache(self, count: int) -> list[str]:
        """Get queries from cache"""
        self._cache_hits += 1
        if self._cache_data is None:
            return []
        return self._cache_data[:count]

    def _cache_articles(self, articles: list[str]) -> None:
        """Cache articles"""
        self._cache_data = articles
        self._cache_time = time.monotonic()

    def _get_api_date(self) -> tuple[str, str, str]:
        """Get yesterday's date for API call (UTC)"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        return (str(yesterday.year), f"{yesterday.month:02d}", f"{yesterday.day:02d}")

    def _build_api_url(self) -> str:
        """Build API URL using constants"""
        base_url = QUERY_SOURCE_URLS["wikipedia_top_views"]
        yyyy, mm, dd = self._get_api_date()
        return f"{base_url}/{self.lang}.wikipedia/all-access/{yyyy}/{mm}/{dd}"

    async def _fetch_top_articles(self, session: aiohttp.ClientSession) -> list[dict[str, Any]]:
        """
        Fetch top articles from Wikipedia API

        Args:
            session: aiohttp session

        Returns:
            List of article objects
        """
        try:
            url = self._build_api_url()
            self.logger.debug(f"Fetching top articles from: {url}")

            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "items" in data and data["items"]:
                        articles = data["items"][0].get("articles", [])
                        self._available = True
                        return list(articles) if articles else []
                else:
                    self.logger.warning(f"Wikipedia API returned status {response.status}")
        except Exception as e:
            self.logger.error(f"Error fetching top articles: {e}")
        return []

    def _filter_articles(self, articles: list[dict]) -> list[str]:
        """
        Filter out non-article entries

        Args:
            articles: List of article objects

        Returns:
            List of filtered article titles
        """
        filtered = []
        for article in articles:
            title = article.get("article", "")
            if not any(title.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
                filtered.append(title.replace("_", " "))
        return filtered

    async def fetch_queries(self, count: int) -> list[str]:
        """
        Fetch queries from Wikipedia Pageviews API

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        if self._is_cache_valid():
            self.logger.debug("Cache hit for Wikipedia top views")
            return self._get_from_cache(count)

        self._cache_misses += 1
        queries = []

        try:
            session = await self._get_session()
            articles = await self._fetch_top_articles(session)

            filtered_articles = self._filter_articles(articles)
            queries = filtered_articles[:count]

            if filtered_articles:
                self._cache_articles(filtered_articles)
                self.logger.debug(f"Cached {len(filtered_articles)} top articles")

            self.logger.debug(f"Fetched {len(queries)} queries from Wikipedia top views")

        except Exception as e:
            self.logger.error(f"Failed to fetch queries from Wikipedia top views: {e}")

        return queries
