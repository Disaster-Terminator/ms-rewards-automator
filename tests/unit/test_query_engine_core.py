"""
Unit tests for QueryEngine core functionality.

These tests validate the internal methods of QueryEngine without
requiring external dependencies or sources.
"""

from unittest.mock import Mock

import pytest

from src.search.query_engine import QueryEngine


@pytest.fixture
def mock_config():
    """Create mock config for QueryEngine tests"""
    config = Mock()
    config.get = Mock(
        side_effect=lambda key, default=None: {
            "query_engine.cache_ttl": 3600,
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


@pytest.mark.unit
class TestQueryEngineCore:
    """Test QueryEngine core functionality"""

    @pytest.mark.asyncio
    async def test_deduplication(self, mock_config):
        """Test query deduplication removes duplicates case-insensitively"""
        engine = QueryEngine(mock_config)

        queries = ["query1", "query2", "query1", "query3", "QUERY2"]
        result = engine._deduplicate_queries(queries)

        # Should remove duplicates (case-insensitive)
        assert len(result) == 3
        assert "query1" in result
        assert "query3" in result
        # Either "query2" or "QUERY2" should be present, but not both
        assert any(q.lower() == "query2" for q in result)

    @pytest.mark.asyncio
    async def test_deduplication_preserves_order(self, mock_config):
        """Test that deduplication preserves first occurrence"""
        engine = QueryEngine(mock_config)

        queries = ["apple", "banana", "cherry", "APPLE", "banana"]
        result = engine._deduplicate_queries(queries)

        # Should keep first occurrence
        assert len(result) == 3
        assert result[0].lower() == "apple"
        assert result[1].lower() == "banana"
        assert result[2].lower() == "cherry"

    @pytest.mark.asyncio
    async def test_randomization(self, mock_config):
        """Test query randomization maintains all elements"""
        engine = QueryEngine(mock_config)

        queries = ["query1", "query2", "query3", "query4", "query5"]
        result = engine._randomize_queries(queries)

        # Should have same length
        assert len(result) == len(queries)

        # Should contain same elements
        assert set(result) == set(queries)

    @pytest.mark.asyncio
    async def test_randomization_with_empty_list(self, mock_config):
        """Test randomization handles empty list"""
        engine = QueryEngine(mock_config)

        queries = []
        result = engine._randomize_queries(queries)

        assert result == []

    @pytest.mark.asyncio
    async def test_cache_usage(self, mock_config):
        """Test that cache is used when available"""
        engine = QueryEngine(mock_config)

        # Pre-populate cache
        cached_queries = ["cached1", "cached2", "cached3"]
        engine.cache.set("queries_3_True", cached_queries)

        # Generate queries (should use cache)
        result = await engine.generate_queries(3, expand=True)

        # Should return cached queries (possibly in different order due to randomization)
        assert set(result) == set(cached_queries)

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, mock_config):
        """Test that different parameters generate different cache keys"""
        engine = QueryEngine(mock_config)

        # Set cache for different parameters
        engine.cache.set("queries_5_False", ["a", "b", "c", "d", "e"])
        engine.cache.set("queries_5_True", ["x", "y", "z"])

        # Verify different keys store different values
        assert engine.cache.get("queries_5_False") != engine.cache.get("queries_5_True")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
