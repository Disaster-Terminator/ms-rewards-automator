"""
Bing Suggestions API client for query expansion
"""

import asyncio
import logging
from urllib.parse import quote

import aiohttp

from constants import QUERY_SOURCE_URLS

logger = logging.getLogger(__name__)


class BingAPIClient:
    """Client for Bing Suggestions API (no authentication required)"""

    SUGGESTIONS_URL = QUERY_SOURCE_URLS["bing_suggestions"]

    def __init__(self, config):
        """
        Initialize Bing API client

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.rate_limit_delay = 60 / config.get("query_engine.bing_api.rate_limit", 10)
        self.last_request_time = 0
        self.max_retries = config.get("query_engine.bing_api.max_retries", 3)
        self.timeout = config.get("query_engine.bing_api.timeout", 15)
        self._session: aiohttp.ClientSession | None = None
        self._semaphore: asyncio.Semaphore | None = None

        logger.debug(
            f"BingAPIClient initialized with rate limit: {self.rate_limit_delay:.2f}s between requests"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for rate limiting"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(1)
        return self._semaphore

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get_suggestions(self, query: str) -> list[str]:
        """
        Get Bing search suggestions for a query

        Args:
            query: Base query string

        Returns:
            List of suggestion strings
        """
        # Rate limiting
        await self._wait_for_rate_limit()

        # Retry with exponential backoff
        for attempt in range(self.max_retries):
            try:
                suggestions = await self._fetch_suggestions(query)
                if suggestions:
                    logger.debug(f"Got {len(suggestions)} suggestions for '{query}'")
                    return suggestions
                else:
                    logger.debug(f"No suggestions returned for '{query}'")
                    return []

            except aiohttp.ClientError as e:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Bing API request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    logger.debug(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for query '{query}'")
                    return []

            except Exception as e:
                logger.error(f"Unexpected error fetching suggestions: {e}")
                return []

        return []

    async def _fetch_suggestions(self, query: str) -> list[str]:
        """
        Fetch suggestions from Bing API

        Args:
            query: Query string

        Returns:
            List of suggestions
        """
        encoded_query = quote(query)
        url = f"{self.SUGGESTIONS_URL}?query={encoded_query}"

        semaphore = await self._get_semaphore()
        async with semaphore:
            session = await self._get_session()
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, list) and len(data) > 1:
                    suggestions = data[1]
                    if isinstance(suggestions, list):
                        return [s for s in suggestions if isinstance(s, str) and s.strip()]

                return []

    async def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limiting"""
        current_time = asyncio.get_running_loop().time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_running_loop().time()

    async def expand_queries(
        self, base_queries: list[str], suggestions_per_query: int = 3
    ) -> list[str]:
        """
        Expand a list of base queries using Bing suggestions

        Args:
            base_queries: List of base query strings
            suggestions_per_query: Number of suggestions to fetch per query

        Returns:
            List of expanded queries (includes base queries + suggestions)
        """
        expanded = list(base_queries)  # Start with base queries

        for query in base_queries:
            suggestions = await self.get_suggestions(query)

            # Take up to suggestions_per_query suggestions
            expanded.extend(suggestions[:suggestions_per_query])

        logger.info(f"Expanded {len(base_queries)} queries to {len(expanded)} queries")
        return expanded
