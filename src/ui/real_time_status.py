"""
实时状态显示模块
在无头模式下提供实时状态更新和进度显示
"""

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


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

        # 状态数据
        self.current_operation = "初始化"
        self.progress = 0
        self.total_steps = 0
        self.start_time = None
        self.estimated_completion = None

        # 搜索统计
        self.desktop_searches_completed = 0
        self.desktop_searches_total = 0
        self.mobile_searches_completed = 0
        self.mobile_searches_total = 0

        # 错误统计
        self.error_count = 0
        self.warning_count = 0

        # 积分信息
        self.initial_points = 0
        self.current_points = 0
        self.points_gained = 0

        # 显示控制
        self.display_thread = None
        self.stop_display = False
        self.update_interval = 2  # 2秒更新一次

        logger.info("实时状态显示器初始化完成")

    def start_display(self):
        """开始实时状态显示"""
        if not self.enabled:
            return

        self.start_time = time.time()
        self.stop_display = False

        # 启动显示线程
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()

        logger.debug("实时状态显示已启动")

    def stop_display_thread(self):
        """停止实时状态显示"""
        if not self.enabled or not self.display_thread:
            return

        self.stop_display = True
        if self.display_thread.is_alive():
            self.display_thread.join(timeout=1)

        logger.debug("实时状态显示已停止")

    def _display_loop(self):
        """显示循环（在单独线程中运行）"""
        while not self.stop_display:
            try:
                self._update_display()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.debug(f"状态显示更新出错: {e}")
                break

    def _update_display(self):
        """更新状态显示"""
        if not self.enabled:
            return

        # 清屏（仅在支持的终端中）
        try:
            import os

            if os.name == "nt":  # Windows
                os.system("cls")
            else:  # Unix/Linux/Mac
                os.system("clear")
        except Exception:
            # 如果清屏失败，使用换行分隔
            print("\n" + "=" * 60)

        # 显示标题
        print("🤖 MS Rewards Automator - 实时状态")
        print("=" * 60)

        # 显示当前操作
        print(f"📋 当前操作: {self.current_operation}")

        # 显示进度
        if self.total_steps > 0:
            progress_percent = (self.progress / self.total_steps) * 100
            progress_bar = self._create_progress_bar(progress_percent)
            print(f"📊 总体进度: {progress_bar} {progress_percent:.1f}%")

        # 显示搜索进度
        if self.desktop_searches_total > 0:
            desktop_percent = (self.desktop_searches_completed / self.desktop_searches_total) * 100
            desktop_bar = self._create_progress_bar(desktop_percent, width=20)
            print(
                f"🖥️  桌面搜索: {desktop_bar} {self.desktop_searches_completed}/{self.desktop_searches_total}"
            )

        if self.mobile_searches_total > 0:
            mobile_percent = (self.mobile_searches_completed / self.mobile_searches_total) * 100
            mobile_bar = self._create_progress_bar(mobile_percent, width=20)
            print(
                f"📱 移动搜索: {mobile_bar} {self.mobile_searches_completed}/{self.mobile_searches_total}"
            )

        if self.current_points is not None and self.current_points > 0:
            print(f"💰 积分状态: {self.current_points} (+{self.points_gained})")

        # 显示时间信息
        if self.start_time:
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_duration(elapsed)
            print(f"⏱️  运行时间: {elapsed_str}")

            if self.estimated_completion:
                remaining = max(0, self.estimated_completion - time.time())
                remaining_str = self._format_duration(remaining)
                print(f"⏳ 预计剩余: {remaining_str}")

        # 显示错误统计
        if self.error_count > 0 or self.warning_count > 0:
            print(f"⚠️  错误/警告: {self.error_count}/{self.warning_count}")

        # 显示当前时间
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

    def update_progress(self, current: int, total: int):
        """
        更新总体进度

        Args:
            current: 当前进度
            total: 总步骤数
        """
        self.progress = current
        self.total_steps = total

        # 估算完成时间
        if self.start_time and current > 0:
            elapsed = time.time() - self.start_time
            estimated_total_time = elapsed * total / current
            self.estimated_completion = self.start_time + estimated_total_time

    def update_desktop_searches(self, completed: int, total: int):
        """
        更新桌面搜索进度

        Args:
            completed: 已完成数量
            total: 总数量
        """
        self.desktop_searches_completed = completed
        self.desktop_searches_total = total

    def update_mobile_searches(self, completed: int, total: int):
        """
        更新移动搜索进度

        Args:
            completed: 已完成数量
            total: 总数量
        """
        self.mobile_searches_completed = completed
        self.mobile_searches_total = total

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
        # 处理 None 值的情况
        if self.current_points is not None and self.initial_points is not None:
            self.points_gained = self.current_points - self.initial_points
        elif self.current_points is not None and self.initial_points is None:
            self.points_gained = 0
        else:
            self.points_gained = 0

    def increment_error_count(self):
        """增加错误计数"""
        self.error_count += 1

    def increment_warning_count(self):
        """增加警告计数"""
        self.warning_count += 1

    def show_completion_summary(self):
        """显示完成摘要"""
        if not self.enabled:
            return

        print("\n" + "=" * 60)
        print("🎉 任务执行完成！")
        print("=" * 60)

        if self.start_time:
            total_time = time.time() - self.start_time
            total_time_str = self._format_duration(total_time)
            print(f"⏱️  总执行时间: {total_time_str}")

        print(f"🖥️  桌面搜索: {self.desktop_searches_completed}/{self.desktop_searches_total}")
        print(f"📱 移动搜索: {self.mobile_searches_completed}/{self.mobile_searches_total}")
        print(f"💰 积分获得: +{self.points_gained}")

        if self.error_count > 0 or self.warning_count > 0:
            print(f"⚠️  错误/警告: {self.error_count}/{self.warning_count}")

        print("=" * 60)

    def show_simple_status(self, message: str):
        """
        显示简单状态消息（不启动线程）

        Args:
            message: 状态消息
        """
        if self.enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")


class StatusManager:
    """状态管理器（单例模式）"""

    _instance = None
    _display = None

    @classmethod
    def get_instance(cls, config=None):
        """获取状态管理器实例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._display = RealTimeStatusDisplay(config)
        return cls._instance

    @classmethod
    def get_display(cls):
        """获取状态显示器实例"""
        if cls._display is None:
            cls._display = RealTimeStatusDisplay()
        return cls._display

    @classmethod
    def start(cls, config=None):
        """启动状态显示"""
        display = cls.get_display()
        if config:
            display.config = config
            display.enabled = config.get("monitoring.real_time_display", True)
        display.start_display()

    @classmethod
    def stop(cls):
        """停止状态显示"""
        if cls._display:
            cls._display.stop_display_thread()

    @classmethod
    def update_operation(cls, operation: str):
        """更新操作状态"""
        if cls._display:
            cls._display.update_operation(operation)

    @classmethod
    def update_progress(cls, current: int, total: int):
        """更新进度"""
        if cls._display:
            cls._display.update_progress(current, total)

    @classmethod
    def update_desktop_searches(cls, completed: int, total: int):
        """更新桌面搜索进度"""
        if cls._display:
            cls._display.update_desktop_searches(completed, total)

    @classmethod
    def update_mobile_searches(cls, completed: int, total: int):
        """更新移动搜索进度"""
        if cls._display:
            cls._display.update_mobile_searches(completed, total)

    @classmethod
    def update_points(cls, current: int, initial: int = None):
        """更新积分信息"""
        if cls._display:
            cls._display.update_points(current, initial)

    @classmethod
    def show_completion(cls):
        """显示完成摘要"""
        if cls._display:
            cls._display.show_completion_summary()
            cls._display.stop_display_thread()
