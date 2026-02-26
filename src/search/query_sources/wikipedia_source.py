"""
Wikipedia Trending query source - fetches trending/popular topics from Wikipedia API
"""

import random

import aiohttp

from constants import QUERY_SOURCE_URLS

from .query_source import QuerySource


class WikipediaSource(QuerySource):
    """Query source that fetches trending topics from Wikipedia API"""

    API_URL = QUERY_SOURCE_URLS["wikipedia_summary"]

    TRENDING_TOPICS = [
        "Artificial_intelligence",
        "Climate_change",
        "Space_exploration",
        "Renewable_energy",
        "Quantum_computing",
        "Electric_vehicle",
        "Cryptocurrency",
        "Virtual_reality",
        "Machine_learning",
        "Blockchain",
        "Internet_of_things",
        "Biotechnology",
        "Nanotechnology",
        "Robotics",
        "Cybersecurity",
        "Sustainable_development",
        "SpaceX",
        "Tesla,_Inc.",
        "Apple_Inc.",
        "Microsoft",
        "Google",
        "Amazon_(company)",
        "Netflix",
        "Meta_Platforms",
        "OpenAI",
    ]

    RANDOM_URL = QUERY_SOURCE_URLS["wikipedia_random"]

    def __init__(self, config):
        """
        Initialize Wikipedia source

        Args:
            config: ConfigManager instance
        """
        super().__init__(config)
        wiki_timeout = config.get("query_engine.sources.wikipedia.timeout")
        bing_timeout = config.get("query_engine.bing_api.timeout", 15)
        self.timeout = wiki_timeout if wiki_timeout is not None else bing_timeout
        self._available = True
        self._session: aiohttp.ClientSession | None = None

        self.logger.info("WikipediaSource initialized")

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
        Fetch queries from Wikipedia API

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        queries = []

        try:
            session = await self._get_session()
            num_topics = min(count, len(self.TRENDING_TOPICS))
            topics = random.sample(self.TRENDING_TOPICS, num_topics)

            for topic in topics:
                if len(queries) >= count:
                    break

                title = await self._fetch_page_title(session, topic)
                if title:
                    queries.append(title)

            while len(queries) < count:
                random_title = await self._fetch_random_page(session)
                if random_title:
                    queries.append(random_title)
                else:
                    break

            queries = queries[:count]
            self.logger.debug(f"Fetched {len(queries)} queries from Wikipedia")
            self._available = True

        except Exception as e:
            self.logger.error(f"Failed to fetch queries from Wikipedia: {e}")
            self._available = False

        return queries

    async def _fetch_page_title(self, session: aiohttp.ClientSession, topic: str) -> str | None:
        """
        Fetch the title of a Wikipedia page

        Args:
            session: aiohttp session
            topic: Topic string

        Returns:
            Page title or None
        """
        try:
            url = f"{self.API_URL}{topic}"

            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    title = data.get("title", "")
                    return title.replace("_", " ") if title else None
                else:
                    return None
        except Exception as e:
            self.logger.debug(f"Error fetching Wikipedia page '{topic}': {e}")
            return None

    async def _fetch_random_page(self, session: aiohttp.ClientSession) -> str | None:
        """
        Fetch a random Wikipedia page title

        Args:
            session: aiohttp session

        Returns:
            Random page title or None
        """
        try:
            async with session.get(
                self.RANDOM_URL, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    title = data.get("title", "")
                    return title.replace("_", " ") if title else None
                else:
                    return None
        except Exception as e:
            self.logger.debug(f"Error fetching random Wikipedia page: {e}")
            return None

    def get_source_name(self) -> str:
        """Return the name of this source"""
        return "wikipedia"

    def is_available(self) -> bool:
        """Check if this source is available"""
        return self._available
