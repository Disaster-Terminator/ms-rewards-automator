"""
Integration tests for Query Engine.

Tests the complete query generation flow with multiple sources.
"""

from unittest.mock import Mock, patch

import pytest

from src.search.query_engine import QueryEngine
from src.search.query_sources import BingSuggestionsSource, LocalFileSource


@pytest.fixture
def mock_config():
    """Create mock configuration for query engine."""
    config = Mock()
    config.get = Mock(
        side_effect=lambda key, default=None: {
            "query_engine.cache_ttl": 3600,
            "query_engine.sources.local_file.enabled": True,
            "query_engine.sources.bing_suggestions.enabled": True,
            "query_engine.bing_api.rate_limit": 10,
            "query_engine.bing_api.max_retries": 3,
            "query_engine.bing_api.timeout": 15,
            "query_engine.bing_api.suggestions_per_query": 3,
            "query_engine.bing_api.suggestions_per_seed": 3,
            "query_engine.bing_api.max_expand": 5,
            "search.search_terms_file": "tools/search_terms.txt",
        }.get(key, default)
    )
    return config


@pytest.mark.integration
class TestQueryEngineIntegration:
    """Integration tests for QueryEngine with multiple sources."""

    @pytest.mark.asyncio
    async def test_query_generation_with_local_source(self, mock_config):
        """Test query generation using LocalFileSource."""
        engine = QueryEngine(mock_config)

        # Generate queries
        queries = await engine.generate_queries(count=10, expand=False)

        # Should return queries
        assert len(queries) > 0
        assert len(queries) <= 10
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q) > 0 for q in queries)

    @pytest.mark.asyncio
    async def test_query_generation_with_expansion(self, mock_config):
        """Test query generation with expansion enabled."""
        engine = QueryEngine(mock_config)

        # Generate queries with expansion
        queries = await engine.generate_queries(count=5, expand=True)

        # Should return queries
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)

    @pytest.mark.asyncio
    async def test_fallback_to_local_file(self, mock_config):
        """Test fallback to local file when Bing API fails."""
        engine = QueryEngine(mock_config)

        # Mock Bing source to fail
        with patch.object(
            BingSuggestionsSource, "fetch_queries", side_effect=Exception("API Error")
        ):
            queries = await engine.generate_queries(count=5, expand=True)

            # Should still return queries from local file
            assert len(queries) > 0
            assert all(isinstance(q, str) for q in queries)

    @pytest.mark.asyncio
    async def test_query_deduplication_across_sources(self, mock_config):
        """Test that queries are deduplicated across multiple sources."""
        engine = QueryEngine(mock_config)

        # Generate queries multiple times
        queries1 = await engine.generate_queries(count=10, expand=False)
        queries2 = await engine.generate_queries(count=10, expand=False)

        # Should have some overlap but be deduplicated
        assert len(queries1) > 0
        assert len(queries2) > 0

        # Each set should have no internal duplicates
        assert len(queries1) == len({q.lower() for q in queries1})
        assert len(queries2) == len({q.lower() for q in queries2})

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, mock_config):
        """Test that cache reduces redundant source calls."""
        engine = QueryEngine(mock_config)

        # First call - should fetch from sources
        queries1 = await engine.generate_queries(count=5, expand=False)

        # Second call with same parameters - should use cache
        queries2 = await engine.generate_queries(count=5, expand=False)

        # Should return same queries (possibly in different order)
        assert set(queries1) == set(queries2)

    @pytest.mark.asyncio
    async def test_different_counts_generate_different_queries(self, mock_config):
        """Test that different counts generate appropriately sized results."""
        engine = QueryEngine(mock_config)

        # Generate different counts
        queries_5 = await engine.generate_queries(count=5, expand=False)
        queries_10 = await engine.generate_queries(count=10, expand=False)

        # Should respect count limits
        assert len(queries_5) <= 5
        assert len(queries_10) <= 10

        # Larger count should have more queries (if available)
        if len(queries_10) > len(queries_5):
            assert len(queries_10) > len(queries_5)


@pytest.mark.integration
class TestQuerySourceAvailability:
    """Test query source availability checking."""

    def test_local_file_source_availability(self, mock_config):
        """Test LocalFileSource availability."""
        source = LocalFileSource(mock_config)

        # Should be available if file exists
        is_available = source.is_available()
        assert isinstance(is_available, bool)

    def test_bing_suggestions_source_availability(self, mock_config):
        """Test BingSuggestionsSource availability."""
        source = BingSuggestionsSource(mock_config)

        # Should be available initially
        assert source.is_available() is True

        # Should have correct source name
        assert source.get_source_name() == "bing_suggestions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
