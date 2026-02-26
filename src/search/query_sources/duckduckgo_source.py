"""
DuckDuckGo Suggestions query source - fetches queries from DuckDuckGo API
"""

import random

import aiohttp

from constants import QUERY_SOURCE_URLS

from .query_source import QuerySource


class DuckDuckGoSource(QuerySource):
    """Query source that fetches suggestions from DuckDuckGo API"""

    API_URL = QUERY_SOURCE_URLS["duckduckgo"]

    SEED_QUERIES = [
        "how to",
        "what is",
        "best way to",
        "why does",
        "when should",
        "where can I",
        "who is",
        "which is better",
        "how do I",
        "what are the",
    ]

    def __init__(self, config):
        """
        Initialize DuckDuckGo source

        Args:
            config: ConfigManager instance
        """
        super().__init__(config)
        self.timeout = config.get("query_engine.sources.duckduckgo.timeout", 15)
        self._available = True
        self._session: aiohttp.ClientSession | None = None

        self.logger.info("DuckDuckGoSource initialized")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def fetch_queries(self, count: int) -> list[str]:
        """
        Fetch queries from DuckDuckGo API

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        queries = []

        try:
            num_seeds = min(count // 3 + 1, len(self.SEED_QUERIES))
            seeds = random.sample(self.SEED_QUERIES, num_seeds)

            session = await self._get_session()
            for seed in seeds:
                if len(queries) >= count:
                    break

                suggestions = await self._fetch_suggestions(session, seed)
                queries.extend(suggestions[:3])

            queries = queries[:count]
            self.logger.debug(f"Fetched {len(queries)} queries from DuckDuckGo")
            self._available = True

        except Exception as e:
            self.logger.error(f"Failed to fetch queries from DuckDuckGo: {e}")
            self._available = False

        return queries

    async def _fetch_suggestions(self, session: aiohttp.ClientSession, query: str) -> list[str]:
        """
        Fetch suggestions for a single query

        Args:
            session: aiohttp session
            query: Query string

        Returns:
            List of suggestion strings
        """
        try:
            params = {"q": query, "kl": "wt-wt"}

            async with session.get(
                self.API_URL, params=params, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [item.get("phrase", "") for item in data if item.get("phrase")]
                else:
                    self.logger.warning(f"DuckDuckGo API returned status {response.status}")
                    return []
        except Exception as e:
            self.logger.debug(f"Error fetching DuckDuckGo suggestions for '{query}': {e}")
            return []

    def get_source_name(self) -> str:
        """Return the name of this source"""
        return "duckduckgo"

    def is_available(self) -> bool:
        """Check if this source is available"""
        return self._available
