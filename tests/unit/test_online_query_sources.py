"""
Tests for DuckDuckGo and Wikipedia query sources
"""

from unittest.mock import MagicMock

import pytest

from search.query_sources.duckduckgo_source import DuckDuckGoSource
from search.query_sources.wikipedia_source import WikipediaSource


class TestDuckDuckGoSource:
    """Test DuckDuckGo query source"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = MagicMock()
        config.get = MagicMock(return_value=15)
        return config

    @pytest.fixture
    def duckduckgo_source(self, mock_config):
        """Create DuckDuckGo source"""
        return DuckDuckGoSource(mock_config)

    def test_source_initialization(self, duckduckgo_source):
        """Test source initialization"""
        assert duckduckgo_source is not None
        assert duckduckgo_source.get_source_name() == "duckduckgo"
        assert duckduckgo_source.is_available() is True

    def test_seed_queries_exist(self, duckduckgo_source):
        """Test that seed queries are defined"""
        assert len(duckduckgo_source.SEED_QUERIES) > 0
        assert "how to" in duckduckgo_source.SEED_QUERIES

    @pytest.mark.asyncio
    async def test_fetch_queries_returns_list(self, duckduckgo_source):
        """Test that fetch_queries returns a list"""
        queries = await duckduckgo_source.fetch_queries(5)
        assert isinstance(queries, list)

    def test_get_source_name(self, duckduckgo_source):
        """Test source name"""
        assert duckduckgo_source.get_source_name() == "duckduckgo"

    def test_availability_flag(self, duckduckgo_source):
        """Test availability flag"""
        assert duckduckgo_source.is_available() is True
        duckduckgo_source._available = False
        assert duckduckgo_source.is_available() is False


class TestWikipediaSource:
    """Test Wikipedia query source"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = MagicMock()
        config.get = MagicMock(return_value=15)
        return config

    @pytest.fixture
    def wikipedia_source(self, mock_config):
        """Create Wikipedia source"""
        return WikipediaSource(mock_config)

    def test_source_initialization(self, wikipedia_source):
        """Test source initialization"""
        assert wikipedia_source is not None
        assert wikipedia_source.get_source_name() == "wikipedia"
        assert wikipedia_source.is_available() is True

    def test_trending_topics_exist(self, wikipedia_source):
        """Test that trending topics are defined"""
        assert len(wikipedia_source.TRENDING_TOPICS) > 0
        assert "Artificial_intelligence" in wikipedia_source.TRENDING_TOPICS

    @pytest.mark.asyncio
    async def test_fetch_queries_returns_list(self, wikipedia_source):
        """Test that fetch_queries returns a list"""
        queries = await wikipedia_source.fetch_queries(5)
        assert isinstance(queries, list)

    def test_get_source_name(self, wikipedia_source):
        """Test source name"""
        assert wikipedia_source.get_source_name() == "wikipedia"

    def test_availability_flag(self, wikipedia_source):
        """Test availability flag"""
        assert wikipedia_source.is_available() is True
        wikipedia_source._available = False
        assert wikipedia_source.is_available() is False


class TestQuerySourceInterface:
    """Test query source interface"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get = MagicMock(return_value=15)
        return config

    def test_duckduckgo_source_name(self, mock_config):
        """Test DuckDuckGo source name"""
        source = DuckDuckGoSource(mock_config)
        assert source.get_source_name() == "duckduckgo"

    def test_wikipedia_source_name(self, mock_config):
        """Test Wikipedia source name"""
        source = WikipediaSource(mock_config)
        assert source.get_source_name() == "wikipedia"

    def test_sources_are_available_by_default(self, mock_config):
        """Test sources are available by default"""
        ddg = DuckDuckGoSource(mock_config)
        wiki = WikipediaSource(mock_config)
        assert ddg.is_available() is True
        assert wiki.is_available() is True
