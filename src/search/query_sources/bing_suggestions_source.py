"""
Bing Suggestions query source - fetches queries from Bing Suggestions API
"""

import random

from ..bing_api_client import BingAPIClient
from .query_source import QuerySource


class BingSuggestionsSource(QuerySource):
    """Query source that fetches suggestions from Bing Suggestions API"""

    SEED_QUERIES = [
        "technology",
        "science",
        "health",
        "travel",
        "food",
        "sports",
        "entertainment",
        "business",
        "education",
        "news",
        "weather",
        "finance",
        "shopping",
        "music",
        "movies",
        "books",
        "games",
        "art",
        "history",
        "culture",
    ]

    def __init__(self, config):
        """
        Initialize Bing Suggestions source

        Args:
            config: ConfigManager instance
        """
        super().__init__(config)
        self._api_client: BingAPIClient | None = None
        self.suggestions_per_seed = config.get("query_engine.bing_api.suggestions_per_seed", 3)
        self._available = True

        self.logger.info("BingSuggestionsSource initialized")

    @property
    def api_client(self) -> BingAPIClient:
        """Get or create API client"""
        if self._api_client is None:
            self._api_client = BingAPIClient(self.config)
        return self._api_client

    async def close(self):
        """Close the API client"""
        if self._api_client:
            await self._api_client.close()
            self._api_client = None

    async def fetch_queries(self, count: int) -> list[str]:
        """
        Fetch queries from Bing Suggestions API

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        queries = []

        try:
            # Randomly select seed queries
            num_seeds = min(count // self.suggestions_per_seed + 1, len(self.SEED_QUERIES))
            seeds = random.sample(self.SEED_QUERIES, num_seeds)

            # Fetch suggestions for each seed
            for seed in seeds:
                if len(queries) >= count:
                    break

                suggestions = await self.api_client.get_suggestions(seed)
                queries.extend(suggestions[: self.suggestions_per_seed])

            # Trim to requested count
            queries = queries[:count]

            self.logger.debug(f"Fetched {len(queries)} queries from Bing Suggestions")
            self._available = True

        except Exception as e:
            self.logger.error(f"Failed to fetch queries from Bing Suggestions: {e}")
            self._available = False

        return queries

    def get_source_name(self) -> str:
        """Return the name of this source"""
        return "bing_suggestions"

    def is_available(self) -> bool:
        """Check if this source is available"""
        return self._available
