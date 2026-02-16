"""
Base classes and data models for the Task System
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Page


@dataclass
class TaskMetadata:
    """Metadata for a Microsoft Rewards task"""

    task_id: str
    task_type: str
    title: str
    points: int
    is_completed: bool
    destination_url: str | None = None
    promotion_type: str | None = None
    is_button: bool = False

    def __str__(self) -> str:
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.title} ({self.points} pts) [{self.task_type}]"


@dataclass
class TaskExecutionReport:
    """Report of task execution results"""

    total_tasks: int
    completed: int
    failed: int
    skipped: int
    points_earned: int
    execution_time: float
    task_details: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Task Execution Report:\n"
            f"  Total: {self.total_tasks}\n"
            f"  Completed: {self.completed}\n"
            f"  Failed: {self.failed}\n"
            f"  Skipped: {self.skipped}\n"
            f"  Points Earned: {self.points_earned}\n"
            f"  Execution Time: {self.execution_time:.2f}s"
        )


class Task(ABC):
    """Abstract base class for all task types"""

    def __init__(self, metadata: TaskMetadata):
        self.metadata = metadata

    @abstractmethod
    async def execute(self, page: Page) -> bool:
        """
        Execute this task

        Args:
            page: Playwright page object

        Returns:
            True if task completed successfully, False otherwise
        """
        pass

    def is_completed(self) -> bool:
        """Check if task is already completed"""
        return self.metadata.is_completed

    def get_points(self) -> int:
        """Get points value of this task"""
        return self.metadata.points

    def get_title(self) -> str:
        """Get task title"""
        return self.metadata.title

    def get_type(self) -> str:
        """Get task type"""
        return self.metadata.task_type

    def __str__(self) -> str:
        return str(self.metadata)
