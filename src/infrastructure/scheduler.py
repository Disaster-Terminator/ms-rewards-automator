"""
任务调度器模块 - 简化版
仅保留 scheduled 模式（定时+随机偏移）
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器类 - 简化版（仅支持 scheduled 模式）"""

    def __init__(self, config):
        """
        初始化任务调度器

        Args:
            config: ConfigManager 实例
        """
        self.config = config

        self.enabled = config.get("scheduler.enabled", True)
        # 保留 mode 配置选项以保证向后兼容，但实际只使用 scheduled
        self.mode = config.get("scheduler.mode", "scheduled")
        self.run_once_on_start = config.get("scheduler.run_once_on_start", True)

        self.timezone_str = config.get("scheduler.timezone", "Asia/Shanghai")
        try:
            if ZoneInfo is not None:
                self.timezone = ZoneInfo(self.timezone_str)
            else:
                logger.warning("zoneinfo 不可用，使用系统本地时区")
                logger.warning("Python 3.8 用户请安装: pip install backports.zoneinfo")
                self.timezone = None
        except Exception as e:
            logger.warning(f"无效时区 '{self.timezone_str}'，使用默认时区: {e}")
            self.timezone = ZoneInfo("Asia/Shanghai") if ZoneInfo else None
            self.timezone_str = "Asia/Shanghai"

        self.scheduled_hour = config.get("scheduler.scheduled_hour", 17)
        self.max_offset_minutes = config.get("scheduler.max_offset_minutes", 45)

        # 测试模式
        self.test_delay_seconds = config.get("scheduler.test_delay_seconds", 0)

        self.running = False
        self.next_run_time = None

        logger.info(f"任务调度器初始化完成 (enabled={self.enabled}, timezone={self.timezone_str})")

    def _get_now(self) -> datetime:
        """获取当前时区的当前时间"""
        if self.timezone:
            return datetime.now(self.timezone)
        return datetime.now()

    def calculate_next_run_time(self) -> datetime:
        """
        计算下次运行时间（仅支持 scheduled 模式）

        Returns:
            下次运行的 datetime 对象（带时区）
        """
        now = self._get_now()

        # 测试模式：立即执行（指定秒后）
        if self.test_delay_seconds > 0:
            target_time = now + timedelta(seconds=self.test_delay_seconds)
            logger.info(
                f"测试模式: 下次运行时间 {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({self.test_delay_seconds}秒后)"
            )
            return target_time

        # 仅支持 scheduled 模式（定时+随机偏移）
        return self._calculate_scheduled_time(now)

    def _calculate_scheduled_time(self, now: datetime) -> datetime:
        """
        计算定时+随机偏移模式的下次运行时间

        用户选择一个整点时间，脚本在该时间 ± max_offset_minutes 范围内随机执行
        """
        scheduled_hour = self.scheduled_hour
        max_offset = self.max_offset_minutes

        offset_minutes = random.randint(-max_offset, max_offset)
        total_minutes = scheduled_hour * 60 + offset_minutes

        actual_hour = total_minutes // 60
        actual_minute = total_minutes % 60

        # 处理跨天情况
        if actual_hour < 0:
            actual_hour += 24
            target_time = now.replace(
                hour=actual_hour, minute=actual_minute, second=0, microsecond=0
            )
            target_time -= timedelta(days=1)
        elif actual_hour >= 24:
            actual_hour -= 24
            target_time = now.replace(
                hour=actual_hour, minute=actual_minute, second=0, microsecond=0
            )
            target_time += timedelta(days=1)
        else:
            target_time = now.replace(
                hour=actual_hour, minute=actual_minute, second=0, microsecond=0
            )

        # 如果时间已过，安排到明天（带新的随机偏移）
        if target_time <= now:
            target_time += timedelta(days=1)
            offset_minutes = random.randint(-max_offset, max_offset)
            total_minutes = scheduled_hour * 60 + offset_minutes
            actual_hour = (total_minutes // 60) % 24
            actual_minute = total_minutes % 60
            tomorrow = now + timedelta(days=1)
            target_time = tomorrow.replace(
                hour=actual_hour, minute=actual_minute, second=0, microsecond=0
            )

        logger.info(
            f"定时调度: 基准时间 {scheduled_hour}:00，偏移 {offset_minutes:+d} 分钟，"
            f"下次运行时间 {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )
        return target_time

    async def wait_until_next_run(self) -> None:
        """等待到下次运行时间"""
        self.next_run_time = self.calculate_next_run_time()

        now = self._get_now()
        wait_seconds = (self.next_run_time - now).total_seconds()
        if wait_seconds < 0:
            wait_seconds = 0

        wait_hours = wait_seconds / 3600
        if wait_hours >= 1:
            logger.info(f"等待 {wait_hours:.2f} 小时后执行任务...")
        else:
            wait_minutes = wait_seconds / 60
            logger.info(f"等待 {wait_minutes:.1f} 分钟后执行任务...")

        while wait_seconds > 0:
            sleep_time = min(wait_seconds, 3600)
            await asyncio.sleep(sleep_time)
            wait_seconds -= sleep_time

            if wait_seconds > 0:
                remaining_hours = wait_seconds / 3600
                if remaining_hours >= 1:
                    logger.debug(f"还需等待 {remaining_hours:.2f} 小时...")
                else:
                    logger.debug(f"还需等待 {wait_seconds / 60:.1f} 分钟...")

    async def run_scheduled_task(self, task_func, run_once_first: bool = True) -> None:
        """
        运行调度任务

        Args:
            task_func: 要执行的任务函数（异步）
            run_once_first: 是否先执行一次再进入调度（默认True）
        """
        if not self.enabled:
            logger.warning("调度器未启用")
            return

        self.running = True
        logger.info("=" * 60)
        logger.info("任务调度器启动")
        logger.info(f"时区: {self.timezone_str}")
        logger.info("=" * 60)

        try:
            if run_once_first and self.run_once_on_start:
                logger.info("⚡ 启动时先执行一次任务...")
                logger.info("=" * 60)
                try:
                    await task_func()
                    logger.info("✓ 首次执行完成")
                except Exception as e:
                    logger.error(f"❌ 首次执行失败: {e}")
                    import traceback

                    traceback.print_exc()
                logger.info("=" * 60)

            while self.running:
                await self.wait_until_next_run()

                logger.info("=" * 60)
                logger.info(
                    f"开始执行定时任务 - {self._get_now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
                )
                logger.info("=" * 60)

                try:
                    await task_func()
                    logger.info("✓ 定时任务执行完成")
                except Exception as e:
                    logger.error(f"❌ 定时任务执行失败: {e}")
                    import traceback

                    traceback.print_exc()

                logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.info("收到中断信号，停止调度器")
            self.running = False
        except Exception as e:
            logger.error(f"调度器异常: {e}")
            self.running = False

    def stop(self) -> None:
        """停止调度器"""
        logger.info("停止任务调度器...")
        self.running = False

    def get_status(self) -> dict:
        """
        获取调度器状态（简化版，仅保留 scheduled 模式信息）

        Returns:
            状态字典
        """
        return {
            "enabled": self.enabled,
            "running": self.running,
            "mode": "scheduled",  # 简化：总是返回 scheduled
            "timezone": self.timezone_str,
            "run_once_on_start": self.run_once_on_start,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "config": {
                "scheduled_hour": self.scheduled_hour,
                "max_offset_minutes": self.max_offset_minutes,
            },
        }
