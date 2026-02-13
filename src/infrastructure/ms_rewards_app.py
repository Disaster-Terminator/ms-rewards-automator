"""
MSRewardsApp - 系统总线

作为应用的主控制器，协调所有子系统组件。
采用门面模式，封装复杂的初始化和执行逻辑。
"""

import asyncio
import logging
from typing import Optional, Any, Dict

from browser.anti_ban_module import AntiBanModule
from browser.simulator import BrowserSimulator
from search.search_term_generator import SearchTermGenerator
from search.search_engine_legacy import SearchEngine
from search.query_engine import QueryEngine
from account.points_detector import PointsDetector
from account.manager import AccountManager
from infrastructure.state_monitor import StateMonitor
from infrastructure.error_handler import ErrorHandler
from infrastructure.notificator import Notificator
from infrastructure.health_monitor import HealthMonitor
from ui.real_time_status import StatusManager
from tasks import TaskManager


class MSRewardsApp:
    """
    MS Rewards 应用主控制器

    负责协调所有子系统，提供统一的生命周期管理。
    """

    def __init__(self, config: Any, args: Any):
        """
        初始化应用

        Args:
            config: ConfigManager 实例
            args: 命令行参数
        """
        self.config = config
        self.args = args
        self.logger = logging.getLogger(self.__class__.__name__)

        # 核心组件（延迟初始化）
        self.browser_sim: Optional[BrowserSimulator] = None
        self.search_engine: Optional[SearchEngine] = None
        self.account_mgr: Optional[AccountManager] = None
        self.state_monitor: Optional[StateMonitor] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.notificator: Optional[Notificator] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.task_manager: Optional[TaskManager] = None

        # 浏览器实例
        self.browser = None
        self.context = None
        self.page = None

        # 初始化器
        from .system_initializer import SystemInitializer
        self.initializer = SystemInitializer(config, args, self.logger)

        # 任务协调器
        from .task_coordinator import TaskCoordinator
        self.coordinator = TaskCoordinator(config, args, self.logger)

    async def run(self) -> int:
        """
        执行主任务流程

        Returns:
            0: 成功
            非0: 失败
        """
        try:
            # 1. 初始化组件
            self.logger.info("\n[1/8] 初始化组件...")
            StatusManager.update_operation("初始化组件")
            await self._init_components()
            StatusManager.update_progress(1, 8)

            # 2. 创建浏览器
            self.logger.info("\n[2/8] 创建浏览器...")
            StatusManager.update_operation("创建浏览器")
            await self._create_browser()
            StatusManager.update_progress(2, 8)

            # 3. 处理登录
            self.logger.info("\n[3/8] 检查登录状态...")
            StatusManager.update_operation("检查登录状态")
            await self._handle_login()
            StatusManager.update_progress(3, 8)

            # 4. 检查初始积分
            self.logger.info("\n[4/8] 检查初始积分...")
            StatusManager.update_operation("检查初始积分")
            await self._check_initial_points()
            StatusManager.update_progress(4, 8)

            # 5-6. 执行搜索
            await self._execute_searches()

            # 7. 执行日常任务
            await self._execute_daily_tasks()

            # 8. 生成报告
            await self._generate_report()

            return 0

        except KeyboardInterrupt:
            self.logger.info("\n\n⚠ 用户中断")
            return 130
        except Exception as e:
            self.logger.error(f"\n❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await self._cleanup()

    async def _init_components(self) -> None:
        """初始化所有组件"""
        self.browser_sim, self.search_engine, self.account_mgr, \
            self.state_monitor, self.error_handler, self.notificator, \
            self.health_monitor = self.initializer.initialize_components()

        # 启动健康监控
        await self.health_monitor.start_monitoring()

    async def _create_browser(self) -> None:
        """创建浏览器实例"""
        self.browser = await self.browser_sim.create_desktop_browser(self.args.browser)
        self.context, self.page = await self.browser_sim.create_context(
            self.browser,
            f"desktop_{self.args.browser}",
            storage_state=self.config.get("account.storage_state_path")
        )

    async def _handle_login(self) -> None:
        """处理登录流程"""
        await self.coordinator.handle_login(self.page, self.context)

    async def _check_initial_points(self) -> None:
        """检查初始积分"""
        initial_points = await self.state_monitor.check_points_before_task(self.page)
        StatusManager.update_points(initial_points, initial_points)

    async def _execute_searches(self) -> None:
        """执行搜索任务"""
        # 5. 桌面搜索
        if not self.args.mobile_only:
            await self.coordinator.execute_desktop_search(self.page)

        # 6. 移动搜索
        if not self.args.desktop_only:
            await self.coordinator.execute_mobile_search(self.page)

    async def _execute_daily_tasks(self) -> None:
        """执行日常任务"""
        if not self.args.skip_daily_tasks:
            await self.coordinator.execute_daily_tasks(self.page)

    async def _generate_report(self) -> None:
        """生成报告和通知"""
        # 7. 生成报告
        self.logger.info("\n[8/8] 生成报告...")
        StatusManager.update_operation("生成报告和发送通知")

        # 保存每日报告
        self.state_monitor.save_daily_report()

        # 获取状态
        state = self.state_monitor.get_account_state()

        # 发送通知
        if self.notificator.enabled and not self.args.dry_run:
            await self._send_notification(state)

        # 显示摘要
        self._show_summary(state)

    async def _send_notification(self, state: Dict) -> None:
        """发送通知"""
        self.logger.info("  发送通知...")
        report_data = {
            "points_gained": state["points_gained"],
            "current_points": state["current_points"],
            "desktop_searches": state["session_data"]["desktop_searches"],
            "mobile_searches": state["session_data"]["mobile_searches"],
            "status": "正常" if state["points_gained"] > 0 else "无积分增加",
            "alerts": state["session_data"]["alerts"]
        }
        await self.notificator.send_daily_report(report_data)

    def _show_summary(self, state: Dict) -> None:
        """显示执行摘要"""
        self.logger.info("\n" + "=" * 70)
        StatusManager.update_progress(8, 8)
        StatusManager.show_completion()
        self.logger.info("执行摘要")
        self.logger.info("=" * 70)
        self.logger.info(f"初始积分: {state['initial_points']:,}" if state['initial_points'] else "初始积分: 未知")
        self.logger.info(f"当前积分: {state['current_points']:,}" if state['current_points'] else "当前积分: 未知")
        self.logger.info(f"获得积分: +{state['points_gained']}")
        self.logger.info(f"桌面搜索: {state['session_data']['desktop_searches']} 次")
        self.logger.info(f"移动搜索: {state['session_data']['mobile_searches']} 次")

        if 'tasks_completed' in state['session_data']:
            self.logger.info(f"完成任务: {state['session_data']['tasks_completed']} 个")
        if 'tasks_failed' in state['session_data']:
            self.logger.info(f"失败任务: {state['session_data']['tasks_failed']} 个")

        self.logger.info(f"告警数量: {len(state['session_data']['alerts'])}")

        # 显示健康状态
        if self.health_monitor.enabled:
            self.logger.info(f"健康状态: {self.health_monitor.get_health_summary()}")
            self.health_monitor.save_health_report()
            perf_report = self.health_monitor.get_performance_report()
            self.logger.info(f"运行时间: {perf_report['uptime_formatted']}")
            self.logger.info(f"搜索成功率: {perf_report['success_rate']*100:.1f}%")
            if perf_report['average_response_time'] > 0:
                self.logger.info(f"平均响应时间: {perf_report['average_response_time']:.2f}s")

        self.logger.info("=" * 70)

    async def _cleanup(self) -> None:
        """清理资源"""
        # 关闭浏览器
        if self.browser_sim:
            self.logger.info("\n关闭浏览器...")
            await self.browser_sim.close()

        # 日志轮替
        self.logger.info("\n清理旧日志和截图...")
        from infrastructure.log_rotation import LogRotation
        rotator = LogRotation()
        rotator.cleanup_all()

        self.logger.info("\n✅ 任务执行完成")
