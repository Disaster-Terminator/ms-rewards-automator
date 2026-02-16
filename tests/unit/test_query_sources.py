"""
Unit tests for Query Sources.

These tests validate individual query source implementations.
"""

from unittest.mock import Mock

import pytest

from src.search.query_sources import BingSuggestionsSource, LocalFileSource


@pytest.fixture
def mock_config_local_file():
    """Create mock config for LocalFileSource"""
    config = Mock()
    config.get = Mock(return_value="tools/search_terms.txt")
    return config


@pytest.fixture
def mock_config_bing():
    """Create mock config for BingSuggestionsSource"""
    config = Mock()
    config.get = Mock(
        side_effect=lambda key, default=None: {
            "query_engine.bing_api.rate_limit": 10,
            "query_engine.bing_api.max_retries": 3,
            "query_engine.bing_api.timeout": 15,
            "query_engine.bing_api.suggestions_per_seed": 3,
        }.get(key, default)
    )
    return config


@pytest.mark.unit
class TestLocalFileSource:
    """Test LocalFileSource functionality"""

    def test_source_initialization(self, mock_config_local_file):
        """Test LocalFileSource initializes correctly"""
        source = LocalFileSource(mock_config_local_file)

        assert source is not None
        assert source.get_source_name() == "local_file"

    def test_source_availability(self, mock_config_local_file):
        """Test LocalFileSource availability check"""
        source = LocalFileSource(mock_config_local_file)

        # Should be available if file exists
        is_available = source.is_available()
        assert isinstance(is_available, bool)

    @pytest.mark.asyncio
    async def test_fetch_queries(self, mock_config_local_file):
        """Test LocalFileSource fetches queries"""
        source = LocalFileSource(mock_config_local_file)

        # Should fetch queries
        queries = await source.fetch_queries(5)

        assert isinstance(queries, list)
        assert len(queries) <= 5
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q) > 0 for q in queries)

    @pytest.mark.asyncio
    async def test_fetch_queries_respects_count(self, mock_config_local_file):
        """Test that fetch_queries respects the count parameter"""
        source = LocalFileSource(mock_config_local_file)

        queries_5 = await source.fetch_queries(5)
        queries_10 = await source.fetch_queries(10)

        assert len(queries_5) <= 5
        assert len(queries_10) <= 10


@pytest.mark.unit
class TestBingSuggestionsSource:
    """Test BingSuggestionsSource functionality"""

    def test_source_initialization(self, mock_config_bing):
        """Test BingSuggestionsSource initializes correctly"""
        source = BingSuggestionsSource(mock_config_bing)

        assert source is not None
        assert source.get_source_name() == "bing_suggestions"

    def test_source_availability(self, mock_config_bing):
        """Test BingSuggestionsSource availability"""
        source = BingSuggestionsSource(mock_config_bing)

        # Should be available initially
        assert source.is_available() is True

    def test_source_name(self, mock_config_bing):
        """Test BingSuggestionsSource returns correct name"""
        source = BingSuggestionsSource(mock_config_bing)

        assert source.get_source_name() == "bing_suggestions"

    def test_rate_limit_configuration(self, mock_config_bing):
        """Test that rate limit is configured from config"""
        BingSuggestionsSource(mock_config_bing)

        # Verify config was read
        mock_config_bing.get.assert_any_call("query_engine.bing_api.rate_limit", 10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
