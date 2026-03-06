"""
实时状态显示模块
在无头模式下提供实时状态更新和进度显示
"""

import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# Module-level singleton instance
_display_instance: "RealTimeStatusDisplay | None" = None


def get_display(config=None) -> "RealTimeStatusDisplay":
    """获取或创建全局显示实例"""
    global _display_instance
    if _display_instance is None:
        _display_instance = RealTimeStatusDisplay(config)
    return _display_instance


class RealTimeStatusDisplay:
    """实时状态显示器类"""

    def __init__(self, config=None):
        """
        初始化实时状态显示器

        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.enabled = config.get("monitoring.real_time_display", True) if config else True

        self.current_operation = "初始化"
        self.progress = 0
        self.total_steps = 0
        self.start_time = None
        self.estimated_completion = None

        self.desktop_searches_completed = 0
        self.desktop_searches_total = 0
        self.mobile_searches_completed = 0
        self.mobile_searches_total = 0

        self.search_times: list[float] = []
        self.max_search_times = 50

        self.error_count = 0
        self.warning_count = 0

        self.initial_points = 0
        self.current_points = 0
        self.points_gained = 0

        logger.info("实时状态显示器初始化完成")

    def start(self):
        """开始实时状态显示"""
        if not self.enabled:
            return

        self.start_time = datetime.now()
        logger.debug("实时状态显示已启动")

    def stop(self):
        """停止实时状态显示"""
        logger.debug("实时状态显示已停止")

    def _update_display(self):
        """更新状态显示（同步）"""
        if not self.enabled:
            return

        desktop_completed = self.desktop_searches_completed
        desktop_total = self.desktop_searches_total
        mobile_completed = self.mobile_searches_completed
        mobile_total = self.mobile_searches_total
        operation = self.current_operation
        current_points = self.current_points
        points_gained = self.points_gained
        error_count = self.error_count
        warning_count = self.warning_count

        if sys.stdout.isatty():
            print("\033[2J\033[H", end="")
        else:
            print("\n" + "=" * 60)

        print("🤖 MS Rewards Automator - 实时状态")
        print("=" * 60)

        print(f"📋 当前操作: {operation}")

        total_searches = desktop_total + mobile_total
        completed_searches = desktop_completed + mobile_completed
        if total_searches > 0:
            search_percent = (completed_searches / total_searches) * 100
            search_bar = self._create_progress_bar(search_percent)
            print(f"📊 搜索进度: {search_bar} {completed_searches}/{total_searches}")

        if desktop_total > 0:
            desktop_percent = (desktop_completed / desktop_total) * 100
            desktop_bar = self._create_progress_bar(desktop_percent, width=20)
            print(f"🖥️  桌面搜索: {desktop_bar} {desktop_completed}/{desktop_total}")

        if mobile_total > 0:
            mobile_percent = (mobile_completed / mobile_total) * 100
            mobile_bar = self._create_progress_bar(mobile_percent, width=20)
            print(f"📱 移动搜索: {mobile_bar} {mobile_completed}/{mobile_total}")

        if current_points is not None and current_points > 0:
            print(f"💰 积分状态: {current_points} (+{points_gained})")

        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            elapsed_str = self._format_duration(elapsed)
            print(f"⏱️  运行时间: {elapsed_str}")

            if completed_searches > 0 and total_searches > 0:
                remaining_searches = total_searches - completed_searches
                if self.search_times:
                    avg_time_per_search = sum(self.search_times) / len(self.search_times)
                else:
                    avg_time_per_search = (
                        elapsed / completed_searches if completed_searches > 0 else 5
                    )

                remaining_time = remaining_searches * avg_time_per_search
                remaining_str = self._format_duration(remaining_time)
                print(f"⏳ 预计剩余: {remaining_str}")

        if error_count > 0 or warning_count > 0:
            print(f"⚠️  错误/警告: {error_count}/{warning_count}")

        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"🕐 当前时间: {current_time}")

        print("=" * 60)
        print("💡 提示: 按 Ctrl+C 可以安全停止程序")

    def _create_progress_bar(self, percent: float, width: int = 30) -> str:
        """
        创建进度条

        Args:
            percent: 百分比 (0-100)
            width: 进度条宽度

        Returns:
            进度条字符串
        """
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def _format_duration(self, seconds: float) -> str:
        """
        格式化时间长度

        Args:
            seconds: 秒数

        Returns:
            格式化的时间字符串
        """
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"

    def update_operation(self, operation: str):
        """
        更新当前操作

        Args:
            operation: 操作描述
        """
        self.current_operation = operation
        logger.info(f"状态更新: {operation}")
        self._update_display()

    def update_progress(self, current: int, total: int):
        """
        更新总体进度

        Args:
            current: 当前进度
            total: 总步骤数
        """
        self.progress = current
        self.total_steps = total
        self._update_display()

    def update_desktop_searches(self, completed: int, total: int, search_time: float = None):
        """
        更新桌面搜索进度

        Args:
            completed: 已完成数量
            total: 总数量
            search_time: 本次搜索耗时（秒）
        """
        self.desktop_searches_completed = completed
        self.desktop_searches_total = total
        if search_time is not None:
            self.search_times.append(search_time)
            if len(self.search_times) > self.max_search_times:
                self.search_times.pop(0)
        self._update_display()

    def update_mobile_searches(self, completed: int, total: int, search_time: float = None):
        """
        更新移动搜索进度

        Args:
            completed: 已完成数量
            total: 总数量
            search_time: 本次搜索耗时（秒）
        """
        self.mobile_searches_completed = completed
        self.mobile_searches_total = total
        if search_time is not None:
            self.search_times.append(search_time)
            if len(self.search_times) > self.max_search_times:
                self.search_times.pop(0)
        self._update_display()

    def update_points(self, current: int, initial: int = None):
        """
        更新积分信息

        Args:
            current: 当前积分
            initial: 初始积分（可选）
        """
        self.current_points = current
        if initial is not None:
            self.initial_points = initial
        if self.current_points is not None and self.initial_points is not None:
            self.points_gained = self.current_points - self.initial_points
        elif self.current_points is not None and self.initial_points is None:
            self.points_gained = 0
        else:
            self.points_gained = 0
        self._update_display()

    def increment_error_count(self):
        """增加错误计数"""
        self.error_count += 1
        self._update_display()

    def increment_warning_count(self):
        """增加警告计数"""
        self.warning_count += 1
        self._update_display()

    def show_completion_summary(self):
        """显示完成摘要"""
        if not self.enabled:
            return

        desktop_completed = self.desktop_searches_completed
        desktop_total = self.desktop_searches_total
        mobile_completed = self.mobile_searches_completed
        mobile_total = self.mobile_searches_total
        points_gained = self.points_gained
        error_count = self.error_count
        warning_count = self.warning_count

        self._safe_print("\n" + "=" * 60)
        self._safe_print("✓ 任务执行完成！")
        self._safe_print("=" * 60)

        if self.start_time:
            total_time = (datetime.now() - self.start_time).total_seconds()
            total_time_str = self._format_duration(total_time)
            self._safe_print(f"总执行时间: {total_time_str}")

        self._safe_print(f"🖥️  桌面搜索: {desktop_completed}/{desktop_total}")
        self._safe_print(f"📱 移动搜索: {mobile_completed}/{mobile_total}")
        self._safe_print(f"💰 积分获得: +{points_gained}")

        if error_count > 0 or warning_count > 0:
            self._safe_print(f"⚠️  错误/警告: {error_count}/{warning_count}")

        self._safe_print("=" * 60)

    def _safe_print(self, message: str):
        """安全打印，处理编码问题"""
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode("ascii", "replace").decode("ascii"))


class StatusManager:
    """状态管理器（简化版）"""

    @classmethod
    def get_display(cls):
        """获取状态显示器实例"""
        return get_display()

    @classmethod
    def start(cls, config=None):
        """启动状态显示"""
        display = get_display(config)
        display.start()

    @classmethod
    def stop(cls):
        """停止状态显示"""
        if _display_instance:
            _display_instance.stop()

    @classmethod
    def update_operation(cls, operation: str):
        """更新操作状态"""
        if _display_instance:
            _display_instance.update_operation(operation)

    @classmethod
    def update_progress(cls, current: int, total: int):
        """更新进度"""
        if _display_instance:
            _display_instance.update_progress(current, total)

    @classmethod
    def update_desktop_searches(cls, completed: int, total: int, search_time: float = None):
        """更新桌面搜索进度"""
        if _display_instance:
            _display_instance.update_desktop_searches(completed, total, search_time)

    @classmethod
    def update_mobile_searches(cls, completed: int, total: int, search_time: float = None):
        """更新移动搜索进度"""
        if _display_instance:
            _display_instance.update_mobile_searches(completed, total, search_time)

    @classmethod
    def update_points(cls, current: int, initial: int = None):
        """更新积分信息"""
        if _display_instance:
            _display_instance.update_points(current, initial)

    @classmethod
    def show_completion(cls):
        """显示完成摘要"""
        if _display_instance:
            _display_instance.show_completion_summary()
            _display_instance.stop()
