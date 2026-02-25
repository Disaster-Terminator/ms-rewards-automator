"""
Mock dashboard fixtures for testing MS Rewards Automator.

Provides mock dashboard data and generators for testing task parsing
and execution functionality.
"""

import copy
from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

fake = Faker()


@dataclass
class MockDashboard:
    """Mock dashboard page for testing."""

    html_content: str
    tasks: list[dict[str, Any]]
    points_available: int


# ============================================================================
# Dashboard Generator
# ============================================================================


def generate_mock_dashboard(num_tasks: int = 5, completed_ratio: float = 0.3) -> MockDashboard:
    """
    Generate a realistic mock dashboard with tasks.

    Args:
        num_tasks: Number of tasks to generate
        completed_ratio: Ratio of tasks that are completed (0.0 to 1.0)

    Returns:
        MockDashboard with generated tasks
    """
    tasks = []
    total_points = 0

    for i in range(num_tasks):
        task_type = fake.random_element(["quiz", "urlreward", "poll"])
        points = fake.random_int(min=1, max=50)
        completed = fake.boolean(chance_of_getting_true=int(completed_ratio * 100))

        task = {
            "id": f"task_{i}",
            "type": task_type,
            "title": fake.sentence(nb_words=6),
            "points": points,
            "completed": completed,
            "url": f"https://example.com/task/{i}",
        }
        tasks.append(task)

        if not completed:
            total_points += points

    # Generate simple HTML representation
    html_content = _generate_dashboard_html(tasks)

    return MockDashboard(html_content=html_content, tasks=tasks, points_available=total_points)


def _generate_dashboard_html(tasks: list[dict[str, Any]]) -> str:
    """Generate simple HTML for dashboard."""
    html_parts = ['<div class="dashboard">']

    for task in tasks:
        status = "completed" if task["completed"] else "available"
        html_parts.append(f'''
            <div class="task {status}" data-task-id="{task["id"]}">
                <span class="task-title">{task["title"]}</span>
                <span class="task-points">{task["points"]} points</span>
                <span class="task-type">{task["type"]}</span>
            </div>
        ''')

    html_parts.append("</div>")
    return "\n".join(html_parts)


# ============================================================================
# Predefined Dashboards
# ============================================================================

# Empty dashboard (no tasks)
EMPTY_DASHBOARD = MockDashboard(
    html_content='<div class="dashboard"></div>', tasks=[], points_available=0
)

# Simple dashboard with 3 tasks
SIMPLE_DASHBOARD = generate_mock_dashboard(num_tasks=3, completed_ratio=0.0)

# Full dashboard with many tasks
FULL_DASHBOARD = generate_mock_dashboard(num_tasks=10, completed_ratio=0.5)


# ============================================================================
# Pytest Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def mock_dashboard_empty():
    """Provide an empty dashboard."""
    return copy.deepcopy(EMPTY_DASHBOARD)


@pytest.fixture(scope="session")
def mock_dashboard_simple():
    """Provide a simple dashboard with 3 tasks."""
    return generate_mock_dashboard(num_tasks=3, completed_ratio=0.0)


@pytest.fixture(scope="session")
def mock_dashboard_full():
    """Provide a full dashboard with 10 tasks."""
    return generate_mock_dashboard(num_tasks=10, completed_ratio=0.5)


@pytest.fixture(scope="session")
def mock_dashboard_generator():
    """Provide the dashboard generator function."""
    return generate_mock_dashboard
