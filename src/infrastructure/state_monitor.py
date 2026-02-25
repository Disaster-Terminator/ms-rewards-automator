"""
状态监控器模块
监控搜索会话，检测积分变化，触发告警
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from browser.page_utils import temp_page

logger = logging.getLogger(__name__)


class StateMonitor:
    """状态监控器类"""

    def __init__(self, config, points_detector):
        """
        初始化状态监控器

        Args:
            config: ConfigManager 实例
            points_detector: PointsDetector 实例
        """
        self.config = config
        self.points_detector = points_detector

        # 监控配置
        self.enabled = config.get("monitoring.enabled", True)
        self.check_interval = config.get("monitoring.check_interval", 5)  # 每5次搜索检查一次
        self.max_no_increase = config.get("monitoring.max_no_increase_count", 3)

        # 状态跟踪
        self.initial_points = None
        self.last_points = None
        self.no_increase_count = 0
        self.search_count = 0
        self.points_history = []

        # 会话数据
        self.session_data = {
            "start_time": None,
            "end_time": None,
            "desktop_searches": 0,
            "mobile_searches": 0,
            "points_gained": 0,
            "alerts": [],
            "status": "running",
        }

        logger.info(
            f"状态监控器初始化完成 (enabled={self.enabled}, check_interval={self.check_interval})"
        )

    async def check_points_before_task(self, page) -> int | None:
        """
        任务开始前检查积分

        Args:
            page: Playwright Page 对象

        Returns:
            当前积分数量
        """
        if not self.enabled:
            logger.debug("监控已禁用，跳过积分检查")
            return None

        logger.info("任务前检查积分（使用独立页面，避免影响主搜索页面）...")

        try:
            async with temp_page(page.context) as monitor_page:
                points = await self.points_detector.get_current_points(monitor_page)

                if points is not None:
                    self.initial_points = points
                    self.last_points = points
                    self.session_data["start_time"] = datetime.now().isoformat()
                    self.points_history.append(
                        {
                            "time": datetime.now().isoformat(),
                            "points": points,
                            "event": "task_start",
                        }
                    )
                    if len(self.points_history) > 100:
                        self.points_history = self.points_history[-100:]
                    logger.info(f"✓ 初始积分: {points:,}")
                    return points
                else:
                    logger.warning("无法获取初始积分")
                    return None
        except Exception as e:
            logger.error(f"检查初始积分失败: {e}")
            return None

    async def check_points_after_searches(self, page, search_type: str = "desktop") -> int | None:
        """
        搜索后检查积分

        Args:
            page: Playwright Page 对象
            search_type: 搜索类型 ("desktop" 或 "mobile")

        Returns:
            当前积分数量
        """
        self.search_count += 1

        if not self.enabled:
            logger.debug(f"监控已禁用，跳过积分检查 (搜索计数: {self.search_count})")
            return None

        # 只在达到检查间隔时检查
        if self.search_count % self.check_interval != 0:
            logger.debug(f"搜索计数: {self.search_count}, 等待下次检查")
            return None

        logger.info(f"检查积分 (已完成 {self.search_count} 次搜索，使用独立页面)...")

        try:
            async with temp_page(page.context) as monitor_page:
                points = await self.points_detector.get_current_points(
                    monitor_page, skip_navigation=True
                )

                if points is not None:
                    self.points_history.append(
                        {
                            "time": datetime.now().isoformat(),
                            "points": points,
                            "event": f"{search_type}_search",
                            "search_count": self.search_count,
                        }
                    )
                    if len(self.points_history) > 100:
                        self.points_history = self.points_history[-100:]

                    if self.last_points is not None:
                        gain = points - self.last_points

                        if gain > 0:
                            logger.info(f"✓ 积分增加: {self.last_points:,} → {points:,} (+{gain})")
                            self.no_increase_count = 0
                        else:
                            self.no_increase_count += 1
                            logger.warning(f"⚠ 积分未增加 (连续 {self.no_increase_count} 次)")

                            self.session_data["alerts"].append(
                                {
                                    "time": datetime.now().isoformat(),
                                    "type": "no_increase",
                                    "message": f"连续 {self.no_increase_count} 次检查积分未增加",
                                    "search_count": self.search_count,
                                }
                            )

                    self.last_points = points
                    return points
                else:
                    logger.warning("无法获取当前积分")
                    return None
        except Exception as e:
            logger.error(f"检查积分失败: {e}")
            return None

    def detect_no_increase(self) -> bool:
        """
        检测积分是否持续未增加

        Returns:
            是否达到告警阈值
        """
        if not self.enabled:
            return False

        if self.no_increase_count >= self.max_no_increase:
            logger.error(
                f"❌ 积分连续 {self.no_increase_count} 次未增加，达到阈值 {self.max_no_increase}"
            )
            return True

        return False

    def alert_and_stop(self, reason: str) -> None:
        """
        触发告警并停止执行

        Args:
            reason: 停止原因
        """
        logger.error("=" * 60)
        logger.error("⚠️  告警触发 - 停止执行")
        logger.error("=" * 60)
        logger.error(f"原因: {reason}")
        logger.error(f"搜索次数: {self.search_count}")
        logger.error(f"连续无增加: {self.no_increase_count}")

        if self.initial_points and self.last_points:
            logger.error(f"积分变化: {self.initial_points:,} → {self.last_points:,}")

        logger.error("=" * 60)

        # 记录告警
        self.session_data["alerts"].append(
            {
                "time": datetime.now().isoformat(),
                "type": "critical",
                "reason": reason,
                "search_count": self.search_count,
                "no_increase_count": self.no_increase_count,
            }
        )

        self.session_data["status"] = "stopped"
        self.session_data["end_time"] = datetime.now().isoformat()

    def get_account_state(self) -> dict:
        """
        获取账户状态摘要

        Returns:
            状态字典
        """
        state = {
            "monitoring_enabled": self.enabled,
            "search_count": self.search_count,
            "no_increase_count": self.no_increase_count,
            "initial_points": self.initial_points,
            "current_points": self.last_points,
            "points_gained": (self.last_points - self.initial_points)
            if (self.initial_points and self.last_points)
            else 0,
            "session_data": self.session_data,
            "points_history": self.points_history,
        }

        return state

    async def monitor_search_session(
        self, page, search_func, search_count: int, search_type: str = "desktop"
    ) -> bool:
        """
        监控搜索会话

        Args:
            page: Playwright Page 对象
            search_func: 搜索函数
            search_count: 搜索次数
            search_type: 搜索类型

        Returns:
            是否成功完成
        """
        if not self.enabled:
            # 如果监控禁用，直接执行搜索
            await search_func(page, search_count)
            return True

        logger.info(f"开始监控 {search_type} 搜索会话 ({search_count} 次)...")

        try:
            # 执行搜索（分批监控）
            for i in range(search_count):
                # 执行单次搜索
                success = await search_func(page, 1)

                if not success:
                    logger.warning(f"搜索 {i + 1} 失败")

                # 每隔 check_interval 次检查积分
                if (i + 1) % self.check_interval == 0:
                    await self.check_points_after_searches(page, search_type)

                    # 检测是否需要停止
                    if self.detect_no_increase():
                        self.alert_and_stop("积分连续未增加，可能已达每日上限或账号受限")
                        return False

            logger.info(f"✓ {search_type} 搜索会话完成")
            return True

        except Exception as e:
            logger.error(f"监控搜索会话失败: {e}")
            self.alert_and_stop(f"监控异常: {e}")
            return False

    def save_daily_report(self, filepath: str = "logs/daily_report.json") -> None:
        """
        保存每日报告

        Args:
            filepath: 报告文件路径
        """
        try:
            # 确保目录存在
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # 完成会话数据
            self.session_data["end_time"] = datetime.now().isoformat()

            if self.initial_points and self.last_points:
                self.session_data["points_gained"] = self.last_points - self.initial_points

            # 读取现有报告
            reports = []
            if Path(filepath).exists():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        reports = json.load(f)
                except Exception:
                    reports = []

            # 添加今天的报告
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat(),
                "session": self.session_data,
                "state": self.get_account_state(),
            }

            reports.append(report)

            # 保存报告
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(reports, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ 每日报告已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存每日报告失败: {e}")
