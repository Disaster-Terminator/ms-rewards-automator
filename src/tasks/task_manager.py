"""
Task Manager for orchestrating task discovery and execution
"""

import logging
import time

from playwright.async_api import Page

from infrastructure.config_manager import ConfigManager
from tasks.task_base import Task, TaskExecutionReport, TaskMetadata
from tasks.task_parser import TaskParser


class TaskManager:
    """Manager for discovering and executing Microsoft Rewards tasks"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.parser = TaskParser(config)  # Pass config to parser
        self.task_registry: dict[str, type[Task]] = {}
        self._register_task_types()

    def _register_task_types(self):
        """Register available task handler types"""
        # Task handlers will be registered here as they are implemented
        # For now, we'll import and register them dynamically
        try:
            from src.tasks.handlers.url_reward_task import UrlRewardTask

            self.task_registry["urlreward"] = UrlRewardTask
        except ImportError:
            self.logger.debug("UrlRewardTask handler not yet implemented")

        try:
            from src.tasks.handlers.quiz_task import QuizTask

            self.task_registry["quiz"] = QuizTask
        except ImportError:
            self.logger.debug("QuizTask handler not yet implemented")

        try:
            from src.tasks.handlers.poll_task import PollTask

            self.task_registry["poll"] = PollTask
        except ImportError:
            self.logger.debug("PollTask handler not yet implemented")

        self.logger.info(f"Registered {len(self.task_registry)} task types")

    async def discover_tasks(self, page: Page) -> list[Task]:
        """
        Navigate to dashboard and discover all available tasks

        Args:
            page: Playwright page object

        Returns:
            List of Task objects
        """
        self.logger.info("Discovering tasks...")

        # Parse tasks from dashboard
        task_metadata_list = await self.parser.discover_tasks(page)

        # Convert metadata to Task objects
        tasks = []
        for metadata in task_metadata_list:
            task = self._create_task_from_metadata(metadata)
            if task:
                tasks.append(task)

        self.logger.info(f"Created {len(tasks)} task objects")
        return tasks

    def _create_task_from_metadata(self, metadata: TaskMetadata) -> Task | None:
        """
        Create a Task object from metadata

        Args:
            metadata: TaskMetadata object

        Returns:
            Task object or None if task type not supported or disabled
        """
        task_type = metadata.task_type

        # Skip zero-point tasks (e.g., sweepstakes, goals)
        if metadata.points == 0:
            self.logger.debug(f"⏭️  跳过0积分任务: {metadata.title}")
            return None

        # Quiz and poll tasks are treated as URL reward tasks (just visit the URL)
        if task_type in ("quiz", "poll"):
            self.logger.debug(f"📝 将{task_type}任务作为URL任务处理: {metadata.title}")
            task_metadata = TaskMetadata(
                task_id=metadata.task_id,
                task_type="urlreward",
                title=metadata.title,
                points=metadata.points,
                is_completed=metadata.is_completed,
                destination_url=metadata.destination_url,
                promotion_type=metadata.promotion_type,
                is_button=metadata.is_button,
            )
            task_type = "urlreward"
        else:
            task_metadata = metadata

        # Check if task type is enabled in config
        task_type_key = task_type.replace("urlreward", "url_reward")  # Handle naming difference
        is_enabled = self.config.get(f"task_system.task_types.{task_type_key}", True)

        if not is_enabled:
            self.logger.debug(f"⏭️  跳过已禁用的任务类型: {task_type} - {task_metadata.title}")
            return None

        if task_type not in self.task_registry:
            self.logger.warning(f"未注册的任务类型: {task_type}")
            return None

        try:
            task_class = self.task_registry[task_type]
            return task_class(task_metadata)
        except Exception as e:
            self.logger.error(f"创建任务对象失败: {e}")
            return None

    async def execute_tasks(
        self, page: Page, tasks: list[Task], skip_completed: bool = True
    ) -> TaskExecutionReport:
        """
        Execute a list of tasks sequentially

        Args:
            page: Playwright page object
            tasks: List of Task objects to execute
            skip_completed: Whether to skip already completed tasks

        Returns:
            TaskExecutionReport with execution results
        """
        self.logger.info(f"Executing {len(tasks)} tasks...")

        start_time = time.time()
        completed = 0
        failed = 0
        skipped = 0
        points_earned = 0
        task_details = []

        # Get delay configuration
        min_delay = self.config.get("task_system.min_delay", 2)
        max_delay = self.config.get("task_system.max_delay", 5)

        for i, task in enumerate(tasks):
            task_type = task.get_type()
            task_title = task.get_title()
            task_points = task.get_points()

            # Enhanced logging with task type and points
            self.logger.info(f"任务 {i + 1}/{len(tasks)}: {task_title}")
            self.logger.info(f"  📋 类型: {task_type} | 积分: {task_points}")

            # Skip completed tasks if configured
            if skip_completed and task.is_completed():
                self.logger.info("  ⏭️  跳过（已完成）")
                skipped += 1
                task_details.append(
                    {
                        "title": task.get_title(),
                        "type": task.get_type(),
                        "points": task.get_points(),
                        "status": "skipped",
                        "reason": "already_completed",
                    }
                )
                continue

            # Execute task with timeout protection
            try:
                # Set a task-level timeout (60 seconds per task)
                import asyncio

                success = await asyncio.wait_for(task.execute(page), timeout=60.0)

                if success:
                    self.logger.info(f"  ✅ 已完成 (+{task.get_points()} 积分)")
                    completed += 1
                    points_earned += task.get_points()
                    task_details.append(
                        {
                            "title": task.get_title(),
                            "type": task.get_type(),
                            "points": task.get_points(),
                            "status": "completed",
                        }
                    )
                else:
                    self.logger.warning("  ❌ 失败")
                    failed += 1
                    task_details.append(
                        {
                            "title": task.get_title(),
                            "type": task.get_type(),
                            "points": task.get_points(),
                            "status": "failed",
                        }
                    )

            except asyncio.TimeoutError:
                self.logger.error("  ⏱️  超时（60秒）")
                failed += 1
                task_details.append(
                    {
                        "title": task.get_title(),
                        "type": task.get_type(),
                        "points": task.get_points(),
                        "status": "timeout",
                    }
                )
            except Exception as e:
                self.logger.error(f"  ❌ 执行任务出错: {e}")
                failed += 1
                task_details.append(
                    {
                        "title": task.get_title(),
                        "type": task.get_type(),
                        "points": task.get_points(),
                        "status": "error",
                        "error": str(e),
                    }
                )

            # Add delay between tasks (except after last task)
            if i < len(tasks) - 1:
                import random

                delay = random.uniform(min_delay, max_delay)
                self.logger.debug(f"  Waiting {delay:.1f}s before next task...")
                await asyncio.sleep(delay)

        execution_time = time.time() - start_time

        report = TaskExecutionReport(
            total_tasks=len(tasks),
            completed=completed,
            failed=failed,
            skipped=skipped,
            points_earned=points_earned,
            execution_time=execution_time,
            task_details=task_details,
        )

        self.logger.info(f"\n{report}")
        return report

    def register_task_type(self, task_type: str, task_class: type[Task]):
        """
        Register a new task type handler

        Args:
            task_type: Task type identifier
            task_class: Task class to handle this type
        """
        self.task_registry[task_type] = task_class
        self.logger.info(f"Registered task type: {task_type}")
