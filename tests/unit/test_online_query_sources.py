"""
Tests for DuckDuckGo and Wikipedia query sources
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

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
        """Test that fetch_queries returns a list with mocked HTTP"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {"phrase": "how to code"},
                {"phrase": "how to learn"},
                {"phrase": "how to cook"},
            ]
        )
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        duckduckgo_source._session = mock_session

        queries = await duckduckgo_source.fetch_queries(5)
        assert isinstance(queries, list)

    @pytest.mark.asyncio
    async def test_fetch_queries_handles_error(self, duckduckgo_source):
        """Test that fetch_queries handles HTTP errors gracefully"""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        mock_session.closed = False

        duckduckgo_source._session = mock_session

        queries = await duckduckgo_source.fetch_queries(5)
        assert isinstance(queries, list)
        assert len(queries) == 0

    @pytest.mark.asyncio
    async def test_fetch_queries_handles_non_200_status(self, duckduckgo_source):
        """Test that fetch_queries handles non-200 status codes"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        duckduckgo_source._session = mock_session

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

    @pytest.mark.asyncio
    async def test_close_session(self, duckduckgo_source):
        """Test that close() properly closes the session"""
        mock_session = AsyncMock()
        mock_session.closed = False
        duckduckgo_source._session = mock_session

        await duckduckgo_source.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_handles_none_session(self, duckduckgo_source):
        """Test that close() handles None session gracefully"""
        duckduckgo_source._session = None
        await duckduckgo_source.close()

    @pytest.mark.asyncio
    async def test_session_reuse_across_multiple_calls(self, duckduckgo_source):
        """Test that multiple fetch_queries() calls reuse the same session"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"phrase": "test query"}])
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        duckduckgo_source._session = mock_session

        await duckduckgo_source.fetch_queries(5)
        await duckduckgo_source.fetch_queries(5)

        assert duckduckgo_source._session is mock_session
        assert mock_session.get.call_count >= 2

    @pytest.mark.asyncio
    async def test_session_recreated_after_close(self, duckduckgo_source):
        """Test that session is recreated after being closed"""
        mock_session = AsyncMock()
        mock_session.closed = True
        duckduckgo_source._session = mock_session

        session = await duckduckgo_source._get_session()
        assert session is not mock_session


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
        """Test that fetch_queries returns a list with mocked HTTP"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"title": "Artificial intelligence"})
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        wikipedia_source._session = mock_session

        queries = await wikipedia_source.fetch_queries(5)
        assert isinstance(queries, list)

    @pytest.mark.asyncio
    async def test_fetch_queries_handles_error(self, wikipedia_source):
        """Test that fetch_queries handles HTTP errors gracefully"""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        mock_session.closed = False

        wikipedia_source._session = mock_session

        queries = await wikipedia_source.fetch_queries(5)
        assert isinstance(queries, list)

    @pytest.mark.asyncio
    async def test_fetch_queries_handles_non_200_status(self, wikipedia_source):
        """Test that fetch_queries handles non-200 status codes"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        wikipedia_source._session = mock_session

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

    @pytest.mark.asyncio
    async def test_close_session(self, wikipedia_source):
        """Test that close() properly closes the session"""
        mock_session = AsyncMock()
        mock_session.closed = False
        wikipedia_source._session = mock_session

        await wikipedia_source.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_handles_none_session(self, wikipedia_source):
        """Test that close() handles None session gracefully"""
        wikipedia_source._session = None
        await wikipedia_source.close()

    @pytest.mark.asyncio
    async def test_session_reuse_across_multiple_calls(self, wikipedia_source):
        """Test that multiple fetch_queries() calls reuse the same session"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"title": "Test article"})
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context)
        mock_session.closed = False

        wikipedia_source._session = mock_session

        await wikipedia_source.fetch_queries(5)
        await wikipedia_source.fetch_queries(5)

        assert wikipedia_source._session is mock_session
        assert mock_session.get.call_count >= 2

    @pytest.mark.asyncio
    async def test_session_recreated_after_close(self, wikipedia_source):
        """Test that session is recreated after being closed"""
        mock_session = AsyncMock()
        mock_session.closed = True
        wikipedia_source._session = mock_session

        session = await wikipedia_source._get_session()
        assert session is not mock_session


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


class TestConfigKeys:
    """Test configuration key handling"""

    def test_duckduckgo_uses_own_timeout_key(self):
        """Test DuckDuckGo source uses its own timeout config key"""
        config = MagicMock()
        config.get = MagicMock(return_value=30)
        source = DuckDuckGoSource(config)
        config.get.assert_called_with("query_engine.sources.duckduckgo.timeout", 15)
        assert source.timeout == 30

    def test_duckduckgo_uses_default_timeout_when_not_configured(self):
        """Test DuckDuckGo source uses default timeout when not configured"""
        config = MagicMock()
        config.get = MagicMock(return_value=15)
        source = DuckDuckGoSource(config)
        assert source.timeout == 15

    def test_wikipedia_uses_own_timeout_key(self):
        """Test Wikipedia source uses its own timeout config key"""
        config = MagicMock()

        def mock_get(key, default=None):
            if key == "query_engine.sources.wikipedia.timeout":
                return 25
            return default

        config.get = MagicMock(side_effect=mock_get)
        source = WikipediaSource(config)
        assert source.timeout == 25

    def test_wikipedia_fallback_to_bing_api_timeout(self):
        """Test Wikipedia source falls back to bing_api timeout"""
        config = MagicMock()

        def mock_get(key, default=None):
            if key == "query_engine.sources.wikipedia.timeout":
                return None
            if key == "query_engine.bing_api.timeout":
                return 20
            return default

        config.get = MagicMock(side_effect=mock_get)
        source = WikipediaSource(config)
        assert source.timeout == 20

    def test_wikipedia_uses_default_timeout_when_no_config(self):
        """Test Wikipedia source uses default when no config available"""
        config = MagicMock()

        def mock_get(key, default=None):
            return default

        config.get = MagicMock(side_effect=mock_get)
        source = WikipediaSource(config)
        assert source.timeout == 15
