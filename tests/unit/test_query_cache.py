"""
Unit tests for QueryCache component.

These tests validate the caching functionality of the Query Engine.
"""

import pytest

from src.search.query_engine import QueryCache


@pytest.mark.unit
class TestQueryCache:
    """Test QueryCache functionality"""

    def test_cache_set_and_get(self):
        """Test setting and getting cached queries"""
        cache = QueryCache(ttl=3600)
        queries = ["query1", "query2", "query3"]

        cache.set("test_key", queries)
        result = cache.get("test_key")

        assert result == queries

    def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = QueryCache(ttl=3600)
        result = cache.get("nonexistent_key")

        assert result is None

    def test_cache_clear(self):
        """Test clearing cache"""
        cache = QueryCache(ttl=3600)
        cache.set("key1", ["query1"])
        cache.set("key2", ["query2"])

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_with_different_keys(self):
        """Test that different keys store different values"""
        cache = QueryCache(ttl=3600)

        cache.set("key1", ["query1", "query2"])
        cache.set("key2", ["query3", "query4"])

        assert cache.get("key1") == ["query1", "query2"]
        assert cache.get("key2") == ["query3", "query4"]
