"""
Query Engine - Intelligent query generation from multiple sources
"""

import asyncio
import logging
import random
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class QueryCache:
    """Simple in-memory cache with TTL and LRU eviction for queries"""

    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default 1 hour)
            max_size: Maximum number of entries (default 100)
        """
        self.ttl = ttl
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.logger = logging.getLogger(f"{__name__}.QueryCache")

    def get(self, key: str) -> list[str] | None:
        """Get cached queries if not expired"""
        if key in self.cache:
            queries, timestamp = self.cache[key]
            if time.monotonic() - timestamp < self.ttl:
                self.cache.move_to_end(key)
                self.logger.debug(f"Cache hit for key: {key}")
                return queries
            else:
                self.logger.debug(f"Cache expired for key: {key}")
                del self.cache[key]
        return None

    def set(self, key: str, queries: list[str]) -> None:
        """Cache queries with current timestamp"""
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.logger.debug("Cache full, evicted oldest entry")
        self.cache[key] = (queries, time.monotonic())
        self.logger.debug(f"Cached {len(queries)} queries for key: {key}")

    def clear(self) -> None:
        """Clear all cached queries"""
        self.cache.clear()
        self.logger.debug("Cache cleared")


class QueryEngine:
    """
    Intelligent query engine that aggregates queries from multiple sources
    """

    def __init__(self, config):
        """
        Initialize query engine

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.sources = []
        self.cache = QueryCache(ttl=config.get("query_engine.cache_ttl", 3600))
        self.logger = logging.getLogger(__name__)

        # Initialize sources
        self._init_sources()

        self.logger.info(f"QueryEngine initialized with {len(self.sources)} sources")

    def _init_sources(self) -> None:
        """Initialize query sources based on configuration"""
        from .query_sources import BingSuggestionsSource, LocalFileSource

        # Always include local file source (fallback)
        try:
            local_source = LocalFileSource(self.config)
            if local_source.is_available():
                self.sources.append(local_source)
                self.logger.info("✓ LocalFileSource enabled")
            else:
                self.logger.warning("LocalFileSource not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize LocalFileSource: {e}")

        # Bing Suggestions source (optional)
        if self.config.get("query_engine.sources.bing_suggestions.enabled", True):
            try:
                bing_source = BingSuggestionsSource(self.config)
                if bing_source.is_available():
                    self.sources.append(bing_source)
                    self.logger.info("✓ BingSuggestionsSource enabled")
                else:
                    self.logger.warning("BingSuggestionsSource not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize BingSuggestionsSource: {e}")
        else:
            self.logger.info("BingSuggestionsSource disabled in config")

    async def generate_queries(self, count: int, expand: bool = True) -> list[str]:
        """
        Generate a list of unique search queries

        Args:
            count: Number of queries to generate
            expand: Whether to expand queries using Bing API

        Returns:
            List of unique query strings
        """
        # Check cache first
        cache_key = f"queries_{count}_{expand}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.debug(f"Returning {len(cached)} cached queries")
            return self._randomize_queries(cached)

        # Fetch from sources
        queries = await self._fetch_from_sources(count)

        # Expand if requested and Bing source is available
        if expand and self._has_bing_source():
            queries = await self._expand_queries(queries)

        # Deduplicate
        queries = self._deduplicate_queries(queries)

        # Randomize order
        queries = self._randomize_queries(queries)

        # Trim to requested count
        queries = queries[:count]

        # Cache the results
        self.cache.set(cache_key, queries)

        self.logger.info(f"Generated {len(queries)} queries from {len(self.sources)} sources")
        return queries

    async def _fetch_from_sources(self, count: int) -> list[str]:
        """
        Fetch queries from all enabled sources concurrently

        Args:
            count: Number of queries to fetch

        Returns:
            List of queries from all sources
        """
        if not self.sources:
            self.logger.error("No query sources available")
            return []

        # Calculate queries per source
        queries_per_source = max(1, count // len(self.sources))

        # Fetch from all sources concurrently
        tasks = [source.fetch_queries(queries_per_source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        all_queries = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Source {self.sources[i].get_source_name()} failed: {result}")
            elif isinstance(result, list):
                all_queries.extend(result)
                self.logger.debug(
                    f"Source {self.sources[i].get_source_name()} returned {len(result)} queries"
                )

        return all_queries

    async def _expand_queries(self, queries: list[str]) -> list[str]:
        """
        Expand queries using Bing Suggestions API

        Args:
            queries: Base queries to expand

        Returns:
            Expanded list of queries
        """
        from .bing_api_client import BingAPIClient

        try:
            api_client = BingAPIClient(self.config)

            # Select a subset of queries to expand (to avoid too many API calls)
            max_to_expand = self.config.get("query_engine.bing_api.max_expand", 5)
            queries_to_expand = random.sample(queries, min(max_to_expand, len(queries)))

            # Expand
            expanded = await api_client.expand_queries(
                queries_to_expand,
                suggestions_per_query=self.config.get(
                    "query_engine.bing_api.suggestions_per_query", 3
                ),
            )

            self.logger.debug(
                f"Expanded {len(queries_to_expand)} queries to {len(expanded)} queries"
            )
            return expanded

        except Exception as e:
            self.logger.error(f"Query expansion failed: {e}")
            return queries  # Return original queries on failure

    def _deduplicate_queries(self, queries: list[str]) -> list[str]:
        """
        Remove duplicate queries while preserving order

        Args:
            queries: List of queries (may contain duplicates)

        Returns:
            List of unique queries
        """
        seen = set()
        unique = []

        for query in queries:
            # Normalize: lowercase and strip whitespace
            normalized = query.lower().strip()

            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(query)  # Keep original case

        self.logger.debug(f"Deduplicated {len(queries)} queries to {len(unique)} unique queries")
        return unique

    def _randomize_queries(self, queries: list[str]) -> list[str]:
        """
        Randomize the order of queries

        Args:
            queries: List of queries

        Returns:
            Randomized list of queries
        """
        randomized = queries.copy()
        random.shuffle(randomized)
        return randomized

    def _has_bing_source(self) -> bool:
        """Check if Bing Suggestions source is available"""
        return any(source.get_source_name() == "bing_suggestions" for source in self.sources)

    def get_statistics(self) -> dict:
        """
        Get query engine statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "sources_count": len(self.sources),
            "sources": [source.get_source_name() for source in self.sources],
            "cache_size": len(self.cache.cache),
            "cache_ttl": self.cache.ttl,
        }
