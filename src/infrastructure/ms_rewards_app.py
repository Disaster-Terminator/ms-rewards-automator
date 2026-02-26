"""
MSRewardsApp - 系统总线

作为应用的主控制器，协调所有子系统组件。
采用门面模式，封装复杂的初始化和执行逻辑。

主要职责：
1. 协调各个子系统组件的生命周期
2. 执行主要的业务流程（登录、搜索、任务）
3. 管理系统资源和状态
4. 提供统一的错误处理和日志记录

与其它模块的关系：
- SystemInitializer: 负责初始化所有组件
- TaskCoordinator: 负责协调具体任务的执行
- 各子系统组件（BrowserSimulator、SearchEngine等）: 被组装和调用
"""

import logging
from typing import Any

from account.manager import AccountManager
from browser.simulator import BrowserSimulator
from constants import BING_URLS
from infrastructure.error_handler import ErrorHandler
from infrastructure.health_monitor import HealthMonitor
from infrastructure.notificator import Notificator
from infrastructure.state_monitor import StateMonitor
from search.search_engine import SearchEngine
from tasks import TaskManager
from ui.real_time_status import StatusManager


class MSRewardsApp:
    """
    MS Rewards 应用主控制器

    采用门面模式(Facade Pattern)封装复杂的子系统交互。
    负责整个应用的生命周期管理，从初始化到清理。

    关键特性：
    - 延迟初始化：只在需要时创建组件实例
    - 依赖注入：通过SystemInitializer组装依赖关系
    - 状态管理：维护当前执行状态和设备信息
    - 错误处理：统一的异常捕获和处理机制

    执行流程：
    1. 初始化组件（依赖注入）
    2. 创建浏览器实例
    3. 处理登录流程
    4. 检查初始积分状态
    5. 执行搜索任务（桌面+移动）
    6. 执行日常任务
    7. 生成报告和通知
    8. 清理资源
    """

    def __init__(self, config: Any, args: Any, diagnose: bool = False):
        """
        初始化应用

        Args:
            config: ConfigManager 实例，包含所有配置信息
            args: 命令行参数对象，影响运行行为
            diagnose: 是否启用诊断模式
        """
        self.config = config
        self.args = args
        self.diagnose = diagnose
        self.logger = logging.getLogger(self.__class__.__name__)

        self.browser_sim: BrowserSimulator | None = None
        self.search_engine: SearchEngine | None = None
        self.account_mgr: AccountManager | None = None
        self.state_monitor: StateMonitor | None = None
        self.error_handler: ErrorHandler | None = None
        self.notificator: Notificator | None = None
        self.health_monitor: HealthMonitor | None = None
        self.task_manager: TaskManager | None = None
        self.diagnosis_reporter = None
        self._page_inspector = None

        self.browser = None
        self.context = None
        self.page = None

        self.current_device = "desktop"

        from .system_initializer import SystemInitializer

        self.initializer = SystemInitializer(config, args, self.logger)

        from .task_coordinator import TaskCoordinator

        self.coordinator = TaskCoordinator(config, args, self.logger, self.browser_sim)

        if self.diagnose:
            try:
                from pathlib import Path

                from diagnosis.inspector import PageInspector
                from diagnosis.reporter import DiagnosisReporter
                from diagnosis.rotation import cleanup_old_diagnoses

                self.diagnosis_reporter = DiagnosisReporter(output_dir="logs/diagnosis")
                self._page_inspector = PageInspector()
                self.logger.info("诊断模式已启用")
                cleanup_old_diagnoses(Path("logs"))
            except ImportError as e:
                module_name = getattr(e, "name", "未知模块")
                self.logger.error(
                    f"诊断模块导入失败，缺失依赖: {module_name}. "
                    "降级策略: 禁用诊断功能，程序继续运行"
                )
                self.diagnose = False
                self.diagnosis_reporter = None
            except (OSError, PermissionError) as e:
                self.logger.error(
                    f"诊断目录初始化失败（文件系统错误）: {e}. 降级策略: 禁用诊断功能，程序继续运行"
                )
                self.diagnose = False
                self.diagnosis_reporter = None
            except Exception as e:
                self.logger.exception(
                    f"诊断模块初始化发生未预期错误: {e.__class__.__name__}: {e}. "
                    "降级策略: 禁用诊断功能，程序继续运行"
                )
                self.diagnose = False
                self.diagnosis_reporter = None

    async def run(self) -> int:
        """
        执行主任务流程

        这是整个应用的主要执行入口，按照预定义的步骤执行所有任务。
        采用异步编程模型，确保浏览器操作的流畅性。

        Returns:
            int: 0表示成功，非0表示失败（130表示用户中断）

        异常处理策略：
        - KeyboardInterrupt: 用户中断，返回130
        - 其他异常: 记录错误日志并重新抛出
        - finally块: 确保资源正确清理
        """
        try:
            # 执行流程分为8个主要步骤，每步都有状态更新
            # 使用StatusManager向UI实时反馈进度

            # 1. 初始化组件
            # 这个步骤会创建所有需要的子系统组件
            self.logger.info("\n[1/8] 初始化组件...")
            StatusManager.update_operation("初始化组件")
            await self._init_components()
            StatusManager.update_progress(1, 8)

            # 2. 创建浏览器实例
            # 根据配置创建桌面或移动浏览器
            self.logger.info("\n[2/8] 创建浏览器...")
            StatusManager.update_operation("创建浏览器")
            await self._create_browser()
            StatusManager.update_progress(2, 8)

            # 3. 处理登录流程
            # 检查已有会话或进行新的登录
            self.logger.info("\n[3/8] 检查登录状态...")
            StatusManager.update_operation("检查登录状态")
            await self._handle_login()
            if self.diagnose:
                await self._diagnose_checkpoint("login")
            StatusManager.update_progress(3, 8)

            # 4. 检查初始积分
            # 记录任务开始前的积分状态
            self.logger.info("\n[4/8] 检查初始积分...")
            StatusManager.update_operation("检查初始积分")
            await self._check_initial_points()
            StatusManager.update_progress(4, 8)

            # 5-6. 执行搜索任务
            # 桌面和移动搜索是主要积分来源
            await self._execute_searches()

            # 7. 执行日常任务
            # 额外的积分来源，如问答、调查等
            await self._execute_daily_tasks()

            # 8. 生成报告
            # 总结任务执行情况并发送通知
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
            if self.diagnose:
                self._print_diagnosis_summary()
            await self._cleanup()

    async def _init_components(self) -> None:
        """
        初始化所有核心组件

        通过SystemInitializer创建所有需要的子系统组件。
        使用依赖注入模式，将组件注入到TaskCoordinator中。

        关键组件：
        - BrowserSimulator: 浏览器管理
        - SearchEngine: 搜索功能
        - AccountManager: 账户管理
        - StateMonitor: 状态监控
        - ErrorHandler: 错误处理
        - Notificator: 通知系统
        - HealthMonitor: 健康监控

        组件注入关系：
        TaskCoordinator <- AccountManager: 登录状态管理
        TaskCoordinator <- SearchEngine: 搜索执行
        TaskCoordinator <- StateMonitor: 状态跟踪
        TaskCoordinator <- HealthMonitor: 性能监控
        TaskCoordinator <- BrowserSimulator: 浏览器操作
        """
        # 使用初始化器创建所有组件
        (
            self.browser_sim,
            self.search_engine,
            self.account_mgr,
            self.state_monitor,
            self.error_handler,
            self.notificator,
            self.health_monitor,
        ) = self.initializer.initialize_components()

        # 将依赖注入到TaskCoordinator中
        # 这是实现松耦合设计的关键步骤
        self.coordinator.set_account_manager(self.account_mgr).set_search_engine(
            self.search_engine
        ).set_state_monitor(self.state_monitor).set_health_monitor(
            self.health_monitor
        ).set_browser_sim(self.browser_sim)

        # 启动健康监控，在后台监控系统状态
        if self.health_monitor.enabled:
            await self.health_monitor.start_monitoring()

    async def _create_browser(self) -> None:
        """创建浏览器实例（确保只创建一个）"""
        if not hasattr(self, "browser") or not self.browser:
            self.logger.info("创建浏览器实例...")
            self.browser = await self.browser_sim.create_desktop_browser(self.args.browser)
            self.context, self.page = await self.browser_sim.create_context(
                self.browser,
                f"desktop_{self.args.browser}",
                storage_state=self.config.get("account.storage_state_path"),
            )

            if self.health_monitor:
                self.health_monitor.register_browser(self.browser, self.context)
                self.logger.debug("已注册浏览器到健康监控器")

            self.logger.info("✓ 浏览器实例创建成功")
        else:
            self.logger.info("✓ 使用现有的浏览器实例")

    async def _handle_login(self) -> None:
        """处理登录流程"""
        await self.coordinator.handle_login(self.page, self.context)

        if await self._is_page_crashed():
            self.logger.warning("  登录检测后页面已崩溃，重建浏览器上下文...")
            await self._recreate_page()

    async def _check_initial_points(self) -> None:
        """检查初始积分"""
        initial_points = await self.state_monitor.check_points_before_task(self.page)
        StatusManager.update_points(initial_points, initial_points)

        if await self._is_page_crashed():
            self.logger.warning("  积分检测后页面已崩溃，重建浏览器上下文...")
            await self._recreate_page()
        else:
            try:
                current_url = self.page.url
                if "login" in current_url.lower() or "oauth" in current_url.lower():
                    self.logger.info("  页面仍在登录页面，导航到 Bing...")
                    await self.page.goto(
                        BING_URLS["home"], wait_until="domcontentloaded", timeout=30000
                    )
            except Exception as e:
                self.logger.warning(f"  导航到 Bing 失败: {e}")

    async def _execute_searches(self) -> None:
        """执行搜索任务"""
        if getattr(self.args, "skip_search", False):
            self.logger.info("\n[5-6/8] 跳过搜索任务（--skip-search）")
            StatusManager.update_progress(6, 8)
            return

        if not self.args.mobile_only:
            if await self._is_page_crashed():
                self.logger.warning("  页面已崩溃，重建浏览器上下文...")
                await self._recreate_page()
            await self.coordinator.execute_desktop_search(self.page)
            if self.diagnose:
                await self._diagnose_checkpoint("search_desktop")

        mobile_count = self.config.get("search.mobile_count", 0)
        if not self.args.desktop_only and mobile_count > 0:
            self.page = await self.coordinator.execute_mobile_search(self.page)
            self.current_device = "desktop"
            if self.diagnose:
                await self._diagnose_checkpoint("search_mobile")
        elif self.args.desktop_only and mobile_count > 0:
            self.logger.info("[6/8] 因 --desktop-only 参数跳过移动搜索")
            StatusManager.update_progress(6, 8)
        elif mobile_count <= 0:
            self.logger.info("[6/8] 移动搜索已禁用 (mobile_count=0)")
            StatusManager.update_progress(6, 8)

    async def _is_page_crashed(self) -> bool:
        """检查页面是否已崩溃"""
        try:
            if self.page is None:
                return True
            if self.page.is_closed():
                return True
            url = self.page.url
            if not url:
                return True
            await self.page.evaluate("() => document.readyState")
            return False
        except Exception as e:
            self.logger.debug(f"页面状态检查失败: {e}")
            return True

    async def _recreate_page(self) -> None:
        """重建页面"""
        try:
            # 关闭旧的上下文
            if self.context:
                await self.context.close()
        except Exception:
            pass

        # 创建新的上下文和页面
        self.context, self.page = await self.browser_sim.create_context(
            self.browser,
            f"desktop_{self.args.browser}",
            storage_state=self.config.get("account.storage_state_path"),
        )
        self.logger.info("  ✓ 浏览器上下文已重建")

    async def _execute_daily_tasks(self) -> None:
        """执行日常任务"""
        if not self.args.skip_daily_tasks:
            self.page = await self.coordinator.execute_daily_tasks(self.page)
            if self.diagnose:
                await self._diagnose_checkpoint("tasks")

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

    async def _send_notification(self, state: dict) -> None:
        """发送通知"""
        self.logger.info("  发送通知...")
        report_data = {
            "points_gained": state["points_gained"],
            "current_points": state["current_points"],
            "desktop_searches": state["session_data"]["desktop_searches"],
            "mobile_searches": state["session_data"]["mobile_searches"],
            "status": "正常" if state["points_gained"] > 0 else "无积分增加",
            "alerts": state["session_data"]["alerts"],
        }
        await self.notificator.send_daily_report(report_data)

    def _show_summary(self, state: dict) -> None:
        """显示执行摘要"""
        self.logger.info("\n" + "=" * 70)
        StatusManager.update_progress(8, 8)
        StatusManager.show_completion()
        self.logger.info("执行摘要")
        self.logger.info("=" * 70)
        self.logger.info(
            f"初始积分: {state['initial_points']:,}"
            if state["initial_points"]
            else "初始积分: 未知"
        )
        self.logger.info(
            f"当前积分: {state['current_points']:,}"
            if state["current_points"]
            else "当前积分: 未知"
        )
        self.logger.info(f"获得积分: +{state['points_gained']}")
        self.logger.info(f"桌面搜索: {state['session_data']['desktop_searches']} 次")
        self.logger.info(f"移动搜索: {state['session_data']['mobile_searches']} 次")

        if "tasks_completed" in state["session_data"]:
            self.logger.info(f"完成任务: {state['session_data']['tasks_completed']} 个")
        if "tasks_failed" in state["session_data"]:
            self.logger.info(f"失败任务: {state['session_data']['tasks_failed']} 个")

        self.logger.info(f"告警数量: {len(state['session_data']['alerts'])}")

        # 显示健康状态
        if self.health_monitor.enabled:
            self.logger.info(f"健康状态: {self.health_monitor.get_health_summary()}")
            self.health_monitor.save_health_report()
            perf_report = self.health_monitor.get_performance_report()
            self.logger.info(f"运行时间: {perf_report['uptime_formatted']}")
            self.logger.info(f"搜索成功率: {perf_report['success_rate'] * 100:.1f}%")
            if perf_report["average_response_time"] > 0:
                self.logger.info(f"平均响应时间: {perf_report['average_response_time']:.2f}s")

        self.logger.info("=" * 70)

    async def _diagnose_checkpoint(self, checkpoint_type: str) -> None:
        """
        执行诊断检查点

        Args:
            checkpoint_type: 检查点类型 (login/search_desktop/search_mobile/tasks)
        """
        if not self.diagnose or not self.page or not self.diagnosis_reporter:
            return

        try:
            issues = await self._page_inspector.inspect_page(self.page)

            success = not any(i.severity.value in ["critical", "error"] for i in issues)

            self.diagnosis_reporter.add_checkpoint(checkpoint_type, issues, success)

            if issues:
                self.logger.info(f"  诊断 [{checkpoint_type}]: 发现 {len(issues)} 个问题")
                for issue in issues[:3]:
                    self.logger.debug(f"    - {issue.title}: {issue.description}")
            else:
                self.logger.debug(f"  诊断 [{checkpoint_type}]: 通过")

        except Exception as e:
            self.logger.debug(f"诊断检查点失败 {checkpoint_type}: {e}")

    def _print_diagnosis_summary(self) -> None:
        """打印诊断摘要"""
        if not self.diagnose or not self.diagnosis_reporter:
            return

        try:
            self.diagnosis_reporter.save_summary()
            self.diagnosis_reporter.print_summary()
        except Exception as e:
            self.logger.warning(f"打印诊断摘要失败: {e}")

    async def _cleanup(self) -> None:
        """清理资源"""
        # 关闭搜索引擎（释放 QueryEngine 资源）
        if self.search_engine:
            try:
                await self.search_engine.close()
            except Exception as e:
                self.logger.debug(f"关闭搜索引擎失败: {e}")

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
