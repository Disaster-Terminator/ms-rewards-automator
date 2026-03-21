"""API 模块

提供面向业务层的统一 API 访问入口，包括仪表盘相关的客户端封装以及数据模型。
该模块聚合了对外公开的主要类型，方便调用方通过 `api` 包进行导入和使用。

主要组件
-------
- ``DashboardClient``: 仪表盘 API 客户端，对外提供高层封装的请求接口
- ``DashboardError``: 仪表盘相关错误类型，用于封装请求或解析过程中的异常
- ``DashboardData``: 仪表盘整体数据模型
- ``UserStatus``: 用户当前状态信息模型
- ``LevelInfo``: 用户等级与经验值等信息模型
- ``SearchCounter`` / ``SearchCounters``: 搜索计数与统计信息模型
- ``Promotion``: 活动与促销信息模型
- ``PunchCard``: 打卡与活跃度相关的数据模型
"""

from .dashboard_client import DashboardClient, DashboardError
from .models import (
    DashboardData,
    LevelInfo,
    Promotion,
    PunchCard,
    SearchCounter,
    SearchCounters,
    UserStatus,
)

__all__ = [
    "DashboardClient",
    "DashboardError",
    "DashboardData",
    "UserStatus",
    "LevelInfo",
    "SearchCounter",
    "SearchCounters",
    "Promotion",
    "PunchCard",
]
