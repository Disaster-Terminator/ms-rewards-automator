"""
Unit tests for TaskManager and Task System components
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tasks.task_base import Task, TaskExecutionReport, TaskMetadata
from tasks.task_manager import TaskManager


class TestTaskMetadata:
    """Tests for TaskMetadata dataclass"""

    def test_metadata_creation(self):
        """Test creating TaskMetadata with all fields"""
        metadata = TaskMetadata(
            task_id="test-123",
            task_type="urlreward",
            title="Test Task",
            points=10,
            is_completed=False,
            destination_url="https://example.com",
            promotion_type="urlreward",
            is_button=True,
        )

        assert metadata.task_id == "test-123"
        assert metadata.task_type == "urlreward"
        assert metadata.title == "Test Task"
        assert metadata.points == 10
        assert not metadata.is_completed
        assert metadata.destination_url == "https://example.com"
        assert metadata.promotion_type == "urlreward"
        assert metadata.is_button

    def test_metadata_defaults(self):
        """Test TaskMetadata default values"""
        metadata = TaskMetadata(
            task_id="test-456",
            task_type="quiz",
            title="Quiz Task",
            points=20,
            is_completed=True,
        )

        assert metadata.destination_url is None
        assert metadata.promotion_type is None
        assert not metadata.is_button

    def test_metadata_str_incomplete(self):
        """Test string representation of incomplete task"""
        metadata = TaskMetadata(
            task_id="test-789",
            task_type="poll",
            title="Poll Task",
            points=5,
            is_completed=False,
        )

        result = str(metadata)
        assert "○" in result
        assert "Poll Task" in result
        assert "5 pts" in result
        assert "[poll]" in result

    def test_metadata_str_completed(self):
        """Test string representation of completed task"""
        metadata = TaskMetadata(
            task_id="test-000",
            task_type="urlreward",
            title="Completed Task",
            points=15,
            is_completed=True,
        )

        result = str(metadata)
        assert "✓" in result
        assert "Completed Task" in result


class TestTaskExecutionReport:
    """Tests for TaskExecutionReport dataclass"""

    def test_report_creation(self):
        """Test creating TaskExecutionReport"""
        report = TaskExecutionReport(
            total_tasks=5,
            completed=3,
            failed=1,
            skipped=1,
            points_earned=30,
            execution_time=45.5,
        )

        assert report.total_tasks == 5
        assert report.completed == 3
        assert report.failed == 1
        assert report.skipped == 1
        assert report.points_earned == 30
        assert report.execution_time == 45.5
        assert report.task_details == []

    def test_report_with_details(self):
        """Test TaskExecutionReport with task details"""
        details = [
            {"title": "Task 1", "status": "completed", "points": 10},
            {"title": "Task 2", "status": "failed", "points": 20},
        ]

        report = TaskExecutionReport(
            total_tasks=2,
            completed=1,
            failed=1,
            skipped=0,
            points_earned=10,
            execution_time=30.0,
            task_details=details,
        )

        assert len(report.task_details) == 2
        assert report.task_details[0]["title"] == "Task 1"

    def test_report_str(self):
        """Test string representation of report"""
        report = TaskExecutionReport(
            total_tasks=3,
            completed=2,
            failed=0,
            skipped=1,
            points_earned=25,
            execution_time=60.0,
        )

        result = str(report)
        assert "Total: 3" in result
        assert "Completed: 2" in result
        assert "Failed: 0" in result
        assert "Skipped: 1" in result
        assert "Points Earned: 25" in result
        assert "60.00s" in result


class TestTaskBase:
    """Tests for Task abstract base class"""

    def test_task_is_completed(self):
        """Test Task.is_completed method"""

        class ConcreteTask(Task):
            async def execute(self, page):
                return True

        metadata = TaskMetadata(
            task_id="test",
            task_type="test",
            title="Test",
            points=10,
            is_completed=True,
        )
        task = ConcreteTask(metadata)

        assert task.is_completed()

    def test_task_get_points(self):
        """Test Task.get_points method"""

        class ConcreteTask(Task):
            async def execute(self, page):
                return True

        metadata = TaskMetadata(
            task_id="test",
            task_type="test",
            title="Test",
            points=50,
            is_completed=False,
        )
        task = ConcreteTask(metadata)

        assert task.get_points() == 50

    def test_task_get_title(self):
        """Test Task.get_title method"""

        class ConcreteTask(Task):
            async def execute(self, page):
                return True

        metadata = TaskMetadata(
            task_id="test",
            task_type="test",
            title="My Task Title",
            points=10,
            is_completed=False,
        )
        task = ConcreteTask(metadata)

        assert task.get_title() == "My Task Title"

    def test_task_get_type(self):
        """Test Task.get_type method"""

        class ConcreteTask(Task):
            async def execute(self, page):
                return True

        metadata = TaskMetadata(
            task_id="test",
            task_type="urlreward",
            title="Test",
            points=10,
            is_completed=False,
        )
        task = ConcreteTask(metadata)

        assert task.get_type() == "urlreward"


class TestTaskManager:
    """Tests for TaskManager class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config manager"""
        config = MagicMock()
        config.get = MagicMock(
            side_effect=lambda key, default=None: {
                "task_system.enabled": True,
                "task_system.debug_mode": True,
                "task_system.min_delay": 1,
                "task_system.max_delay": 2,
                "task_system.task_types.url_reward": True,
                "task_system.task_types.quiz": True,
                "task_system.task_types.poll": True,
            }.get(key, default)
        )
        return config

    def test_task_manager_init(self, mock_config):
        """Test TaskManager initialization"""
        manager = TaskManager(mock_config)

        assert manager.config == mock_config
        assert manager.parser is not None
        assert isinstance(manager.task_registry, dict)

    def test_task_manager_register_task_type(self, mock_config):
        """Test registering a new task type"""

        class DummyTask(Task):
            async def execute(self, page):
                return True

        manager = TaskManager(mock_config)
        initial_count = len(manager.task_registry)

        manager.register_task_type("dummy", DummyTask)

        assert len(manager.task_registry) == initial_count + 1
        assert "dummy" in manager.task_registry
        assert manager.task_registry["dummy"] == DummyTask

    def test_task_manager_create_task_skips_zero_points(self, mock_config):
        """Test that zero-point tasks are skipped"""
        manager = TaskManager(mock_config)

        metadata = TaskMetadata(
            task_id="zero-points",
            task_type="urlreward",
            title="Zero Point Task",
            points=0,
            is_completed=False,
        )

        result = manager._create_task_from_metadata(metadata)
        assert result is None

    def test_task_manager_creates_puzzle_task(self, mock_config):
        """Test that puzzle tasks are created (puzzle is just a URL task)"""
        manager = TaskManager(mock_config)

        metadata = TaskMetadata(
            task_id="puzzle-task",
            task_type="urlreward",
            title="Daily Puzzle Challenge",
            points=10,
            is_completed=False,
        )

        result = manager._create_task_from_metadata(metadata)
        assert result is not None
        assert result.get_type() == "urlreward"

    def test_task_manager_converts_quiz_to_urlreward(self, mock_config):
        """Test that quiz tasks are converted to urlreward tasks"""
        manager = TaskManager(mock_config)

        metadata = TaskMetadata(
            task_id="quiz-task",
            task_type="quiz",
            title="Daily Quiz Challenge",
            points=10,
            is_completed=False,
        )

        result = manager._create_task_from_metadata(metadata)
        assert result is not None
        assert result.get_type() == "urlreward"

    def test_task_manager_create_task_skips_unregistered_type(self, mock_config):
        """Test that unregistered task types return None"""
        manager = TaskManager(mock_config)

        metadata = TaskMetadata(
            task_id="unknown-task",
            task_type="unknown_type",
            title="Unknown Task",
            points=10,
            is_completed=False,
        )

        result = manager._create_task_from_metadata(metadata)
        assert result is None

    @pytest.mark.asyncio
    async def test_task_manager_discover_tasks(self, mock_config):
        """Test task discovery"""
        manager = TaskManager(mock_config)

        mock_page = AsyncMock()

        mock_metadata = [
            TaskMetadata(
                task_id="task-1",
                task_type="urlreward",
                title="URL Task",
                points=10,
                is_completed=False,
                destination_url="https://example.com",
            ),
        ]

        with patch.object(
            manager.parser, "discover_tasks", new_callable=AsyncMock
        ) as mock_discover:
            mock_discover.return_value = mock_metadata

            tasks = await manager.discover_tasks(mock_page)

            mock_discover.assert_called_once_with(mock_page)
            assert len(tasks) <= len(mock_metadata)

    @pytest.mark.asyncio
    async def test_task_manager_execute_tasks_empty_list(self, mock_config):
        """Test executing empty task list"""
        manager = TaskManager(mock_config)
        mock_page = AsyncMock()

        report = await manager.execute_tasks(mock_page, [])

        assert report.total_tasks == 0
        assert report.completed == 0
        assert report.failed == 0
        assert report.skipped == 0
        assert report.points_earned == 0

    @pytest.mark.asyncio
    async def test_task_manager_execute_tasks_skip_completed(self, mock_config):
        """Test skipping completed tasks"""

        class DummyTask(Task):
            async def execute(self, page):
                return True

        manager = TaskManager(mock_config)
        manager.task_registry["dummy"] = DummyTask

        mock_page = AsyncMock()

        completed_metadata = TaskMetadata(
            task_id="completed-task",
            task_type="dummy",
            title="Completed Task",
            points=10,
            is_completed=True,
        )
        completed_task = DummyTask(completed_metadata)

        report = await manager.execute_tasks(mock_page, [completed_task], skip_completed=True)

        assert report.skipped == 1
        assert report.completed == 0
        assert report.points_earned == 0

    @pytest.mark.asyncio
    async def test_task_manager_execute_tasks_timeout(self, mock_config):
        """Test task execution timeout handling"""

        class SlowTask(Task):
            async def execute(self, page):
                import asyncio

                await asyncio.sleep(70)
                return True

        manager = TaskManager(mock_config)

        mock_page = AsyncMock()

        slow_metadata = TaskMetadata(
            task_id="slow-task",
            task_type="dummy",
            title="Slow Task",
            points=10,
            is_completed=False,
        )
        slow_task = SlowTask(slow_metadata)

        report = await manager.execute_tasks(mock_page, [slow_task])

        assert report.failed == 1
        assert any(d["status"] == "timeout" for d in report.task_details)


class TestTaskManagerIntegration:
    """Integration tests for TaskManager"""

    @pytest.fixture
    def config(self):
        """Create a real config manager for integration tests"""
        from infrastructure.config_manager import ConfigManager

        return ConfigManager()

    def test_task_manager_with_real_config(self, config):
        """Test TaskManager with real configuration"""
        manager = TaskManager(config)

        assert manager.parser is not None
        assert isinstance(manager.task_registry, dict)
