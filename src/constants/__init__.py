"""
常量模块

提供应用程序中使用的集中化常量。

导出:
- URL 常量 (来自 urls.py)
"""

from .urls import (
    API_ENDPOINTS,
    BING_URLS,
    GITHUB_URLS,
    HEALTH_CHECK_URLS,
    LOGIN_URLS,
    NOTIFICATION_URLS,
    QUERY_SOURCE_URLS,
    REWARDS_URLS,
)

__all__ = [
    "API_ENDPOINTS",
    "BING_URLS",
    "GITHUB_URLS",
    "HEALTH_CHECK_URLS",
    "LOGIN_URLS",
    "NOTIFICATION_URLS",
    "QUERY_SOURCE_URLS",
    "REWARDS_URLS",
]
