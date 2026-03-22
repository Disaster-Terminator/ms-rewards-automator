"""Environment detection utilities for E2E tests."""

import os


def is_ci_environment() -> bool:
    """Check if running in CI environment."""
    return any(
        os.environ.get(var)
        for var in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "JENKINS_URL"]
    )


def is_local_development() -> bool:
    """Check if running in local development environment."""
    return not is_ci_environment()


def get_environment_type() -> str:
    """Get current environment type."""
    if is_ci_environment():
        return "ci"
    elif is_local_development():
        return "local"
    else:
        return "unknown"
