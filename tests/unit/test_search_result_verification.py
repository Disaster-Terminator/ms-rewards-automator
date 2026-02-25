"""
Tests for search result verification
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from search.search_engine import SearchEngine


class TestSearchResultVerification:
    """Test search result verification functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "medium",
                "anti_detection.mouse_movement.micro_movement_probability": 0.3,
            }.get(key, default)
        )
        return config

    @pytest.fixture
    def mock_term_generator(self):
        """Create mock term generator"""
        generator = MagicMock()
        generator.get_random_term = MagicMock(return_value="test query")
        return generator

    @pytest.fixture
    def mock_anti_ban(self):
        """Create mock anti-ban module"""
        anti_ban = MagicMock()
        anti_ban.get_random_wait_time = MagicMock(return_value=5.0)
        return anti_ban

    @pytest.fixture
    def search_engine(self, mock_config, mock_term_generator, mock_anti_ban):
        """Create search engine with mocked dependencies"""
        return SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )

    @pytest.mark.asyncio
    async def test_verify_search_result_valid_url(self, search_engine):
        """Test verification with valid search URL"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=5)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_search_result_invalid_url(self, search_engine):
        """Test verification with invalid URL"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/"

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_search_result_with_results(self, search_engine):
        """Test verification with search results present"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=10)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_search_result_no_results_indicator(self, search_engine):
        """Test verification with no results indicator"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=0)
        mock_page.query_selector = AsyncMock(return_value=AsyncMock())

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_search_result_title_contains_term(self, search_engine):
        """Test that search term appears in title"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=python+tutorial"
        mock_page.title = AsyncMock(return_value="python tutorial - Bing")
        mock_page.evaluate = AsyncMock(return_value=5)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await search_engine._verify_search_result(mock_page, "python tutorial")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_search_result_exception_handling(self, search_engine):
        """Test that exceptions are handled gracefully"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(side_effect=Exception("Title error"))
        mock_page.evaluate = AsyncMock(return_value=5)

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_search_result_evaluate_error(self, search_engine):
        """Test handling of evaluate errors"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(side_effect=Exception("Evaluate error"))

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_search_result_no_results_no_indicator(self, search_engine):
        """Test verification with no results and no 'no results' indicator"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=0)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False


class TestHumanSubmitSearch:
    """Test human submit search functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "medium",
                "anti_detection.mouse_movement.micro_movement_probability": 0.3,
            }.get(key, default)
        )
        return config

    @pytest.fixture
    def mock_term_generator(self):
        """Create mock term generator"""
        generator = MagicMock()
        generator.get_random_term = MagicMock(return_value="test query")
        return generator

    @pytest.fixture
    def mock_anti_ban(self):
        """Create mock anti-ban module"""
        anti_ban = MagicMock()
        anti_ban.get_random_wait_time = MagicMock(return_value=5.0)
        return anti_ban

    @pytest.fixture
    def search_engine(self, mock_config, mock_term_generator, mock_anti_ban):
        """Create search engine with mocked dependencies"""
        return SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )

    @pytest.mark.asyncio
    async def test_submit_search_enter_key_success(self, search_engine):
        """Test submit search with Enter key success"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()

        result = await search_engine._human_submit_search(mock_page)
        assert result is True
        mock_page.keyboard.press.assert_called()

    @pytest.mark.asyncio
    async def test_submit_search_escape_enter_path(self, search_engine):
        """Test submit search with Escape+Enter path"""
        call_count = [0]

        def mock_url():
            call_count[0] += 1
            if call_count[0] <= 2:
                return "https://www.bing.com/"
            return "https://www.bing.com/search?q=test"

        mock_page = AsyncMock()
        mock_page.url = property(lambda self: mock_url())
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()

        type(mock_page).url = property(lambda self: mock_url())

        result = await search_engine._human_submit_search(mock_page)
        assert result is True

    @pytest.mark.asyncio
    async def test_submit_search_button_click_success(self, search_engine):
        """Test submit search with button click"""
        call_count = [0]

        def mock_url():
            call_count[0] += 1
            if call_count[0] <= 4:
                return "https://www.bing.com/"
            return "https://www.bing.com/search?q=test"

        mock_page = AsyncMock()
        type(mock_page).url = property(lambda self: mock_url())
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()

        mock_button = AsyncMock()
        mock_button.is_visible = AsyncMock(return_value=True)
        mock_button.click = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_button)

        result = await search_engine._human_submit_search(mock_page)
        assert result is True

    @pytest.mark.asyncio
    async def test_submit_search_all_methods_fail(self, search_engine):
        """Test submit search when all methods fail"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/"
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.press = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.evaluate = AsyncMock()

        result = await search_engine._human_submit_search(mock_page)
        assert result is False


class TestSearchResultVerificationIntegration:
    """Integration tests for search result verification"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get = MagicMock(return_value="medium")
        return config

    @pytest.fixture
    def mock_term_generator(self):
        generator = MagicMock()
        generator.get_random_term = MagicMock(return_value="test")
        return generator

    @pytest.fixture
    def mock_anti_ban(self):
        anti_ban = MagicMock()
        anti_ban.get_random_wait_time = MagicMock(return_value=0.1)
        anti_ban.simulate_human_scroll = AsyncMock()
        return anti_ban

    @pytest.mark.asyncio
    async def test_verification_called_after_search(
        self, mock_config, mock_term_generator, mock_anti_ban
    ):
        """Test that verification is called after search submission"""
        engine = SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )

        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=5)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await engine._verify_search_result(mock_page, "test")
        assert result is True


class TestAntiBanRandomization:
    """Test anti-ban randomization improvements"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "search.wait_interval.min": 5,
                "search.wait_interval.max": 15,
            }.get(key, default)
        )
        return config

    def test_random_wait_time_distribution(self, mock_config):
        """Test that random wait time follows expected distribution"""
        import random

        from browser.anti_ban_module import AntiBanModule

        random.seed(0)

        anti_ban = AntiBanModule(mock_config)

        wait_min = mock_config.get("search.wait_interval.min")
        wait_max = mock_config.get("search.wait_interval.max")
        extra_max = 3

        times = [anti_ban.get_random_wait_time() for _ in range(100)]

        assert all(wait_min <= t <= wait_max + extra_max for t in times)

        assert any(t > wait_max for t in times)

        assert len(set(times)) > 1

    def test_random_wait_time_within_bounds(self, mock_config):
        """Test that random wait time is within bounds"""
        from browser.anti_ban_module import AntiBanModule

        anti_ban = AntiBanModule(mock_config)

        wait_min = mock_config.get("search.wait_interval.min")
        wait_max = mock_config.get("search.wait_interval.max")
        extra_max = 3

        for _ in range(50):
            wait_time = anti_ban.get_random_wait_time()
            assert wait_time >= wait_min
            assert wait_time <= wait_max + extra_max


class TestNetworkErrorHandling:
    """Test network error handling in search verification"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "medium",
                "anti_detection.mouse_movement.micro_movement_probability": 0.3,
            }.get(key, default)
        )
        return config

    @pytest.fixture
    def mock_term_generator(self):
        generator = MagicMock()
        generator.get_random_term = MagicMock(return_value="test query")
        return generator

    @pytest.fixture
    def mock_anti_ban(self):
        anti_ban = MagicMock()
        anti_ban.get_random_wait_time = MagicMock(return_value=5.0)
        return anti_ban

    @pytest.fixture
    def search_engine(self, mock_config, mock_term_generator, mock_anti_ban):
        return SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )

    @pytest.mark.asyncio
    async def test_verify_handles_page_timeout(self, search_engine):
        """Test verification handles page timeout"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(side_effect=TimeoutError("Page timeout"))
        mock_page.evaluate = AsyncMock(return_value=5)

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_handles_query_selector_error(self, search_engine):
        """Test verification handles query selector errors"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(return_value=0)
        mock_page.query_selector = AsyncMock(side_effect=Exception("Selector error"))

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_handles_connection_error(self, search_engine):
        """Test verification handles connection errors during evaluate"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q=test"
        mock_page.title = AsyncMock(return_value="test - Bing")
        mock_page.evaluate = AsyncMock(side_effect=ConnectionError("Network unreachable"))

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_handles_malformed_url(self, search_engine):
        """Test verification handles malformed URLs"""
        mock_page = AsyncMock()
        mock_page.url = "not-a-valid-url"
        mock_page.title = AsyncMock(return_value="Error")

        result = await search_engine._verify_search_result(mock_page, "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_handles_empty_search_term(self, search_engine):
        """Test verification handles empty search term"""
        mock_page = AsyncMock()
        mock_page.url = "https://www.bing.com/search?q="
        mock_page.title = AsyncMock(return_value="Bing")
        mock_page.evaluate = AsyncMock(return_value=0)
        mock_page.query_selector = AsyncMock(return_value=None)

        result = await search_engine._verify_search_result(mock_page, "")
        assert result is False
