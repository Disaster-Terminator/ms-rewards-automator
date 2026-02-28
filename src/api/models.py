"""Dashboard API 数据模型"""

import re
from dataclasses import dataclass, field
from typing import Any, TypeVar

_T = TypeVar("_T")

_CAMEL_TO_SNAKE_PATTERN = re.compile(r"([a-z0-9])([A-Z])")


def _camel_to_snake(name: str) -> str:
    """将 camelCase 转换为 snake_case"""
    return _CAMEL_TO_SNAKE_PATTERN.sub(r"\1_\2", name).lower()


def _transform_dict(data: Any) -> Any:
    """递归转换字典键为 snake_case"""
    if isinstance(data, dict):
        return {_camel_to_snake(k): _transform_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_transform_dict(item) for item in data]
    else:
        return data


def _filter_dataclass_fields(data: dict[str, Any], cls: type[_T]) -> dict[str, Any]:
    """过滤 dataclass 字段，只保留已声明的字段"""
    allowed = cls.__dataclass_fields__.keys()  # type: ignore[attr-defined]
    return {k: v for k, v in data.items() if k in allowed}


@dataclass
class SearchCounter:
    """搜索计数器"""

    progress: int = 0
    max_progress: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchCounter":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class SearchCounters:
    """搜索计数器集合"""

    pc_search: list[SearchCounter] = field(default_factory=list)
    mobile_search: list[SearchCounter] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchCounters":
        """从字典创建实例"""
        data = _transform_dict(data)

        pc_raw = data.get("pc_search") or []
        if not isinstance(pc_raw, list):
            pc_raw = []

        mobile_raw = data.get("mobile_search") or []
        if not isinstance(mobile_raw, list):
            mobile_raw = []

        pc_search = [SearchCounter.from_dict(item) for item in pc_raw if isinstance(item, dict)]
        mobile_search = [
            SearchCounter.from_dict(item) for item in mobile_raw if isinstance(item, dict)
        ]
        return cls(pc_search=pc_search, mobile_search=mobile_search)


@dataclass
class LevelInfo:
    """会员等级信息"""

    active_level: str = ""
    active_level_name: str = ""
    progress: int = 0
    progress_max: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LevelInfo":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class Promotion:
    """推广任务"""

    promotion_type: str = ""
    title: str = ""
    points: int = 0
    status: str = ""
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Promotion":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class PunchCard:
    """打卡任务"""

    name: str = ""
    progress: int = 0
    max_progress: int = 0
    completed: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PunchCard":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class StreakPromotion:
    """连胜推广任务"""

    promotion_type: str = ""
    title: str = ""
    points: int = 0
    status: str = ""
    url: str | None = None
    streak_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StreakPromotion":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class StreakBonusPromotion:
    """连胜奖励推广"""

    promotion_type: str = ""
    title: str = ""
    points: int = 0
    status: str = ""
    url: str | None = None
    streak_day: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StreakBonusPromotion":
        """从字典创建实例"""
        data = _transform_dict(data)
        return cls(**_filter_dataclass_fields(data, cls))


@dataclass
class UserStatus:
    """用户状态"""

    available_points: int = 0
    level_info: LevelInfo = field(default_factory=LevelInfo)
    counters: SearchCounters = field(default_factory=SearchCounters)
    bing_star_monthly_bonus_progress: int = 0
    bing_star_monthly_bonus_maximum: int = 0
    default_search_engine_monthly_bonus_progress: int = 0
    default_search_engine_monthly_bonus_maximum: int = 0
    default_search_engine_monthly_bonus_state: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserStatus":
        """从字典创建实例"""
        data = _transform_dict(data)
        level_info_raw = data.get("level_info")
        level_info = (
            LevelInfo.from_dict(level_info_raw) if isinstance(level_info_raw, dict) else LevelInfo()
        )
        counters_raw = data.get("counters")
        counters = (
            SearchCounters.from_dict(counters_raw)
            if isinstance(counters_raw, dict)
            else SearchCounters()
        )
        return cls(
            available_points=data.get("available_points", 0),
            level_info=level_info,
            counters=counters,
            bing_star_monthly_bonus_progress=data.get("bing_star_monthly_bonus_progress", 0),
            bing_star_monthly_bonus_maximum=data.get("bing_star_monthly_bonus_maximum", 0),
            default_search_engine_monthly_bonus_progress=data.get(
                "default_search_engine_monthly_bonus_progress", 0
            ),
            default_search_engine_monthly_bonus_maximum=data.get(
                "default_search_engine_monthly_bonus_maximum", 0
            ),
            default_search_engine_monthly_bonus_state=data.get(
                "default_search_engine_monthly_bonus_state", ""
            ),
        )


@dataclass
class DashboardData:
    """Dashboard 数据"""

    user_status: UserStatus = field(default_factory=UserStatus)
    daily_set_promotions: dict[str, list[Promotion]] = field(default_factory=dict)
    more_promotions: list[Promotion] = field(default_factory=list)
    punch_cards: list[PunchCard] = field(default_factory=list)
    streak_promotion: StreakPromotion | None = None
    streak_bonus_promotions: list[StreakBonusPromotion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DashboardData":
        """从字典创建实例"""
        data = _transform_dict(data)
        user_status = UserStatus.from_dict(data.get("user_status", {}))

        daily_set_promotions_data = data.get("daily_set_promotions") or {}
        if not isinstance(daily_set_promotions_data, dict):
            daily_set_promotions_data = {}
        daily_set: dict[str, list[Promotion]] = {}
        for key, items in daily_set_promotions_data.items():
            if isinstance(items, list):
                daily_set[key] = [Promotion.from_dict(item) for item in items]

        more_promotions_data = data.get("more_promotions") or []
        if not isinstance(more_promotions_data, list):
            more_promotions_data = []
        more_promotions = [
            Promotion.from_dict(item) for item in more_promotions_data if isinstance(item, dict)
        ]

        punch_cards_data = data.get("punch_cards") or []
        if not isinstance(punch_cards_data, list):
            punch_cards_data = []
        punch_cards = [
            PunchCard.from_dict(item) for item in punch_cards_data if isinstance(item, dict)
        ]

        streak_promotion = None
        streak_promotion_raw = data.get("streak_promotion")
        if isinstance(streak_promotion_raw, dict):
            streak_promotion = StreakPromotion.from_dict(streak_promotion_raw)

        streak_bonus_data = data.get("streak_bonus_promotions") or []
        if not isinstance(streak_bonus_data, list):
            streak_bonus_data = []
        streak_bonus_promotions = [
            StreakBonusPromotion.from_dict(item)
            for item in streak_bonus_data
            if isinstance(item, dict)
        ]

        return cls(
            user_status=user_status,
            daily_set_promotions=daily_set,
            more_promotions=more_promotions,
            punch_cards=punch_cards,
            streak_promotion=streak_promotion,
            streak_bonus_promotions=streak_bonus_promotions,
        )
