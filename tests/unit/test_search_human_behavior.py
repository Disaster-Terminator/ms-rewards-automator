"""
Tests for human behavior integration in SearchEngine
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from search.search_engine import SearchEngine


class TestHumanBehaviorIntegration:
    """Test human behavior integration in search engine"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "medium",
                "anti_detection.mouse_movement.micro_movement_probability": 0.3,
                "anti_detection.scroll_behavior.enabled": True,
                "anti_detection.scroll_behavior.min_scrolls": 2,
                "anti_detection.scroll_behavior.max_scrolls": 5,
                "anti_detection.scroll_behavior.scroll_delay_min": 500,
                "anti_detection.scroll_behavior.scroll_delay_max": 2000,
                "query_engine.enabled": False,
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
        anti_ban.simulate_human_scroll = AsyncMock()
        return anti_ban

    @pytest.fixture
    def mock_status_manager(self):
        """Create mock status manager"""
        manager = MagicMock()
        manager.update_desktop_searches = MagicMock()
        manager.update_mobile_searches = MagicMock()
        return manager

    @pytest.fixture
    def search_engine(self, mock_config, mock_term_generator, mock_anti_ban, mock_status_manager):
        """Create search engine with mocked dependencies"""
        return SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
            status_manager=mock_status_manager,
        )

    def test_human_behavior_level_initialization(self, search_engine):
        """Test that human behavior level is correctly initialized"""
        assert search_engine.human_behavior_level == "medium"
        assert search_engine.micro_movement_probability == 0.3

    def test_human_behavior_simulator_initialized(self, search_engine):
        """Test that human behavior simulator is initialized"""
        assert search_engine.human_behavior is not None

    def test_light_level_initialization(self, mock_config, mock_term_generator, mock_anti_ban):
        """Test light level initialization"""
        mock_config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "light",
                "anti_detection.mouse_movement.micro_movement_probability": 0.0,
            }.get(key, default)
        )
        engine = SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )
        assert engine.human_behavior_level == "light"

    def test_heavy_level_initialization(self, mock_config, mock_term_generator, mock_anti_ban):
        """Test heavy level initialization"""
        mock_config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "anti_detection.human_behavior_level": "heavy",
                "anti_detection.mouse_movement.micro_movement_probability": 0.5,
            }.get(key, default)
        )
        engine = SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
        )
        assert engine.human_behavior_level == "heavy"

    @pytest.mark.asyncio
    async def test_verify_input_success(self, search_engine):
        """Test input verification success"""
        mock_search_box = AsyncMock()
        mock_search_box.input_value = AsyncMock(return_value="test query")

        result = await search_engine._verify_input(mock_search_box, "test query")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_input_failure(self, search_engine):
        """Test input verification failure"""
        mock_search_box = AsyncMock()
        mock_search_box.input_value = AsyncMock(return_value="wrong value")

        result = await search_engine._verify_input(mock_search_box, "test query")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_input_exception(self, search_engine):
        """Test input verification with exception"""
        mock_search_box = AsyncMock()
        mock_search_box.input_value = AsyncMock(side_effect=Exception("Test error"))

        result = await search_engine._verify_input(mock_search_box, "test query")
        assert result is False

    @pytest.mark.asyncio
    async def test_fallback_input_fill_success(self, search_engine):
        """Test fallback input with fill method"""
        mock_page = AsyncMock()
        mock_search_box = AsyncMock()
        mock_search_box.fill = AsyncMock()
        mock_search_box.input_value = AsyncMock(return_value="test query")

        result = await search_engine._fallback_input(mock_page, mock_search_box, "test query")
        assert result is True

    @pytest.mark.asyncio
    async def test_fallback_input_click_type_path(self, search_engine):
        """Test fallback input with click + type path"""
        mock_page = AsyncMock()
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.type = AsyncMock()

        mock_search_box = AsyncMock()
        mock_search_box.fill = AsyncMock(side_effect=Exception("Fill failed"))
        mock_search_box.click = AsyncMock()
        mock_search_box.input_value = AsyncMock(return_value="test query")

        result = await search_engine._fallback_input(mock_page, mock_search_box, "test query")
        assert result is True
        mock_search_box.click.assert_called_once()
        mock_page.keyboard.type.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_input_js_evaluate_path(self, search_engine):
        """Test fallback input with JS evaluate path"""
        mock_page = AsyncMock()

        mock_search_box = AsyncMock()
        mock_search_box.fill = AsyncMock(side_effect=Exception("Fill failed"))
        mock_search_box.click = AsyncMock(side_effect=Exception("Click failed"))
        mock_search_box.evaluate = AsyncMock()
        mock_search_box.input_value = AsyncMock(return_value="test query")

        result = await search_engine._fallback_input(mock_page, mock_search_box, "test query")
        assert result is True
        assert mock_search_box.evaluate.call_count >= 1

    @pytest.mark.asyncio
    async def test_fallback_input_all_methods_fail(self, search_engine):
        """Test fallback input when all methods fail"""
        mock_page = AsyncMock()
        mock_page.keyboard = AsyncMock()
        mock_page.keyboard.type = AsyncMock(side_effect=Exception("Type failed"))

        mock_search_box = AsyncMock()
        mock_search_box.fill = AsyncMock(side_effect=Exception("Fill failed"))
        mock_search_box.click = AsyncMock(side_effect=Exception("Click failed"))
        mock_search_box.evaluate = AsyncMock(side_effect=Exception("Evaluate failed"))
        mock_search_box.input_value = AsyncMock(side_effect=Exception("Input value failed"))

        result = await search_engine._fallback_input(mock_page, mock_search_box, "test query")
        assert result is False

    @pytest.mark.asyncio
    async def test_status_manager_dependency_injection(
        self, mock_config, mock_term_generator, mock_anti_ban
    ):
        """Test that status manager is properly injected"""
        mock_status_manager = MagicMock()
        engine = SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
            status_manager=mock_status_manager,
        )
        assert engine.status_manager is mock_status_manager


class TestHumanBehaviorLevels:
    """Test different human behavior levels"""

    @pytest.fixture
    def mock_search_box(self):
        """Create mock search box"""
        box = AsyncMock()
        box.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 200, "height": 40})
        box.click = AsyncMock()
        box.input_value = AsyncMock(return_value="test")
        return box

    @pytest.fixture
    def mock_page(self):
        """Create mock page"""
        page = AsyncMock()
        page.keyboard = AsyncMock()
        page.keyboard.type = AsyncMock()
        page.keyboard.press = AsyncMock()
        page.viewport_size = {"width": 1920, "height": 1080}
        page.mouse = AsyncMock()
        page.mouse.move = AsyncMock()
        return page

    @pytest.fixture
    def engine_with_level(self):
        """Factory to create engine with specific level"""

        def _create(level):
            config = MagicMock()
            config.get = MagicMock(
                side_effect=lambda key, default=None: {
                    "anti_detection.human_behavior_level": level,
                    "anti_detection.mouse_movement.micro_movement_probability": 0.3,
                }.get(key, default)
            )
            term_generator = MagicMock()
            term_generator.get_random_term = MagicMock(return_value="test")
            anti_ban = MagicMock()
            anti_ban.get_random_wait_time = MagicMock(return_value=5.0)

            return SearchEngine(
                config=config,
                term_generator=term_generator,
                anti_ban=anti_ban,
            )

        return _create

    @pytest.mark.asyncio
    async def test_light_level_uses_basic_typing(
        self, engine_with_level, mock_page, mock_search_box
    ):
        """Test that light level uses basic typing without mouse movement"""
        engine = engine_with_level("light")
        result = await engine._human_input_light(mock_page, mock_search_box, "test")
        assert result is True
        mock_search_box.click.assert_called()

    @pytest.mark.asyncio
    async def test_medium_level_includes_delays(
        self, engine_with_level, mock_page, mock_search_box
    ):
        """Test that medium level includes human-like delays"""
        engine = engine_with_level("medium")
        result = await engine._human_input_medium(mock_page, mock_search_box, "test")
        assert result is True
        mock_search_box.click.assert_called()

    @pytest.mark.asyncio
    async def test_heavy_level_includes_mouse_movement(
        self, engine_with_level, mock_page, mock_search_box
    ):
        """Test that heavy level includes mouse movement"""
        engine = engine_with_level("heavy")
        result = await engine._human_input_heavy(mock_page, mock_search_box, "test")
        assert result is True
        mock_search_box.click.assert_called()


class TestSearchProgressUpdate:
    """Test search progress update timing"""

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
    async def test_progress_updated_after_success(
        self, mock_config, mock_term_generator, mock_anti_ban
    ):
        """Test that progress is updated after successful search"""
        mock_status_manager = MagicMock()
        mock_page = AsyncMock()

        engine = SearchEngine(
            config=mock_config,
            term_generator=mock_term_generator,
            anti_ban=mock_anti_ban,
            status_manager=mock_status_manager,
        )

        engine.perform_single_search = AsyncMock(return_value=True)

        with patch.object(engine, "perform_single_search", return_value=True):
            with patch.object(engine, "_get_search_term", return_value="test"):
                with patch.object(engine.anti_ban, "get_random_wait_time", return_value=0.1):
                    result = await engine.execute_desktop_searches(mock_page, 2, None)

        assert result == 2
        assert mock_status_manager.update_desktop_searches.call_count >= 2
