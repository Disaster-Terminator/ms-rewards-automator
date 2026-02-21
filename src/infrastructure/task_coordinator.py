"""
TaskCoordinator - 任务协调器 (依赖注入版)

负责协调和执行各类任务的逻辑。
使用依赖注入接收依赖项，提高可测试性和可维护性。
"""

import argparse
import logging
from typing import TYPE_CHECKING, Any, Optional

from playwright.async_api import BrowserContext, Page

from browser.page_utils import temp_page as create_temp_page
from ui.real_time_status import StatusManager

if TYPE_CHECKING:
    from account.manager import AccountManager
    from browser.simulator import BrowserSimulator
    from infrastructure.config_manager import ConfigManager
    from infrastructure.health_monitor import HealthMonitor
    from infrastructure.state_monitor import StateMonitor
    from search.search_engine import SearchEngine


class TaskCoordinator:
    """
    任务协调器

    负责协调搜索、登录、任务执行等具体逻辑。
    通过依赖注入接收所有依赖项。
    """

    def __init__(
        self,
        config: "ConfigManager",
        args: argparse.Namespace,
        logger: logging.Logger,
        account_manager: Optional["AccountManager"] = None,
        search_engine: Optional["SearchEngine"] = None,
        state_monitor: Optional["StateMonitor"] = None,
        health_monitor: Optional["HealthMonitor"] = None,
        browser_sim: Optional["BrowserSimulator"] = None,
    ):
        """
        初始化任务协调器

        Args:
            config: ConfigManager 实例
            args: 命令行参数
            logger: 日志记录器
            account_manager: AccountManager 实例（可选，依赖注入）
            search_engine: SearchEngine 实例（可选，依赖注入）
            state_monitor: StateMonitor 实例（可选，依赖注入）
            health_monitor: HealthMonitor 实例（可选，依赖注入）
            browser_sim: BrowserSimulator 实例（可选，依赖注入）
        """
        self.config = config
        self.args = args
        self.logger = logger

        self._account_manager = account_manager
        self._search_engine = search_engine
        self._state_monitor = state_monitor
        self._health_monitor = health_monitor
        self._browser_sim = browser_sim

    def set_account_manager(self, account_manager: "AccountManager") -> "TaskCoordinator":
        """设置 AccountManager（支持链式调用）"""
        self._account_manager = account_manager
        return self

    def set_search_engine(self, search_engine: "SearchEngine") -> "TaskCoordinator":
        """设置 SearchEngine"""
        self._search_engine = search_engine
        return self

    def set_state_monitor(self, state_monitor: "StateMonitor") -> "TaskCoordinator":
        """设置 StateMonitor"""
        self._state_monitor = state_monitor
        return self

    def set_health_monitor(self, health_monitor: "HealthMonitor") -> "TaskCoordinator":
        """设置 HealthMonitor"""
        self._health_monitor = health_monitor
        return self

    def set_browser_sim(self, browser_sim: "BrowserSimulator") -> "TaskCoordinator":
        """设置 BrowserSimulator"""
        self._browser_sim = browser_sim
        return self

    async def handle_login(self, page: Page, context: BrowserContext) -> None:
        """
        处理登录流程

        Args:
            page: Playwright Page 对象
            context: BrowserContext 对象
        """
        account_mgr = self._get_account_manager()

        # 检查是否有会话文件
        has_session = account_mgr.session_exists()

        if has_session:
            is_logged_in = await account_mgr.is_logged_in(page, navigate=True)
        else:
            self.logger.info("  未检测到会话文件，需要登录")
            is_logged_in = False

        if not is_logged_in:
            await self._do_login(page, account_mgr, context)
        else:
            self.logger.info("  ✓ 已登录")

        StatusManager.update_progress(3, 8)

    def _check_headless_requirements(self) -> None:
        """检查 headless 模式下的登录要求

        Headless 模式无法进行手动登录，需要提前准备会话文件或配置自动登录。
        """
        if getattr(self.args, "headless", False):
            self.logger.error(
                "Headless 模式下无法进行手动登录。"
                "解决方案：1) 先在有头模式下登录保存会话；"
                "2) 配置自动登录凭据（login.auto_login）"
            )
            raise RuntimeError(
                "Headless 模式需要会话文件或自动登录配置。请先运行 `rscore`（有头模式）完成登录。"
            )

    async def _do_login(self, page: Any, account_mgr: Any, context: Any) -> None:
        """执行登录流程"""
        import os

        self.logger.warning("  未登录，需要登录")

        if account_mgr.use_state_machine:
            auto_login_config = self.config.get("login.auto_login", {})
            auto_login_enabled = auto_login_config.get("enabled", False)

            email = (
                os.environ.get("MS_REWARDS_EMAIL")
                or auto_login_config.get("email", "")
                or self.config.get("account.email", "")
            )
            password = (
                os.environ.get("MS_REWARDS_PASSWORD")
                or auto_login_config.get("password", "")
                or self.config.get("account.password", "")
            )
            totp_secret = (
                os.environ.get("MS_REWARDS_TOTP_SECRET")
                or auto_login_config.get("totp_secret", "")
                or self.config.get("account.totp_secret", "")
            )

            if auto_login_enabled and email and password:
                self.logger.info("  尝试自动登录...")
                StatusManager.update_operation("自动登录")

                credentials = {"email": email, "password": password, "totp_secret": totp_secret}

                login_success = await account_mgr.auto_login(page, credentials)

                if login_success:
                    self.logger.info("  ✓ 自动登录成功")
                    await account_mgr.save_session(context)
                    self.logger.info("  ✓ 会话已保存")
                else:
                    self._check_headless_requirements()
                    await self._manual_login(page, account_mgr, context)
            else:
                self._check_headless_requirements()
                await self._manual_login(page, account_mgr, context)
        else:
            self._check_headless_requirements()
            await self._manual_login(page, account_mgr, context)

    async def _manual_login(self, page: Any, account_mgr: Any, context: Any) -> None:
        """执行手动登录"""
        self.logger.info("  未启用自动登录或未配置凭据，使用手动登录")
        StatusManager.update_operation("等待手动登录")
        manual_login_success = await account_mgr.wait_for_manual_login(page)

        if manual_login_success:
            await account_mgr.save_session(context)
            self.logger.info("  ✓ 手动登录完成，会话已保存")
        else:
            self.logger.error("  ✗ 手动登录失败或超时")
            raise Exception("登录失败")

    async def execute_desktop_search(
        self,
        page: Any,
    ) -> None:
        """执行桌面搜索"""
        search_engine = self._get_search_engine()
        state_monitor = self._get_state_monitor()
        health_monitor = self._get_health_monitor()

        self.logger.info("\n[5/8] 执行桌面搜索...")
        StatusManager.update_operation("执行桌面搜索")
        desktop_count = self.config.get("search.desktop_count")
        StatusManager.update_desktop_searches(0, desktop_count)

        if self.args.dry_run:
            self.logger.info(f"  [模拟] 将执行 {desktop_count} 次桌面搜索")
        else:
            success = await search_engine.execute_desktop_searches(
                page, desktop_count, health_monitor
            )

            if success:
                self.logger.info(f"  ✓ 桌面搜索完成 ({desktop_count} 次)")
                StatusManager.update_desktop_searches(desktop_count, desktop_count)
            else:
                self.logger.warning("  ⚠ 桌面搜索部分失败")

            # 检查积分
            await state_monitor.check_points_after_searches(page, "desktop")

        StatusManager.update_progress(5, 8)

    async def execute_mobile_search(
        self,
        page: Any,
    ) -> Any:
        """执行移动搜索"""
        search_engine = self._get_search_engine()
        state_monitor = self._get_state_monitor()
        health_monitor = self._get_health_monitor()
        browser_sim = self._get_browser_sim()
        mobile_count = self.config.get("search.mobile_count", 0)

        self.logger.info("\n[6/8] 执行移动搜索...")
        StatusManager.update_operation("执行移动搜索")
        StatusManager.update_mobile_searches(0, mobile_count)

        if self.args.dry_run:
            self.logger.info(f"  [模拟] 将执行 {mobile_count} 次移动搜索")
        else:
            # 复用同一浏览器进程，创建移动浏览器上下文
            self.logger.info("  使用现有浏览器实例，创建移动浏览器上下文...")
            StatusManager.update_operation("创建移动浏览器上下文")

            # 关闭桌面上下文（释放资源，避免多窗口）
            desktop_context = page.context
            try:
                if desktop_context:
                    await desktop_context.close()
                    self.logger.debug("  已关闭桌面上下文")
            except Exception as e:
                self.logger.debug(f"  关闭桌面上下文时出错: {e}")

            from account.manager import AccountManager

            context, page = await browser_sim.create_context(
                browser_sim.browser,
                "mobile_iphone",
                storage_state=self.config.get("account.storage_state_path"),
            )

            # 验证移动端登录状态
            self.logger.info("  验证移动端登录状态...")
            account_mgr = AccountManager(self.config)
            mobile_logged_in = await account_mgr.is_logged_in(page, navigate=False)
            if not mobile_logged_in:
                self.logger.warning("  移动端未登录，后续搜索可能不计积分")

            StatusManager.update_operation("执行移动搜索")
            success = await search_engine.execute_mobile_searches(
                page, mobile_count, health_monitor
            )

            if success:
                self.logger.info(f"  ✓ 移动搜索完成 ({mobile_count} 次)")
                StatusManager.update_mobile_searches(mobile_count, mobile_count)
            else:
                self.logger.warning("  ⚠ 移动搜索部分失败")

            # 检查积分
            await state_monitor.check_points_after_searches(page, "mobile")

            # 移动搜索完成后，切换回桌面上下文并返回桌面页面
            self.logger.info("  移动搜索完成，切换回桌面上下文...")
            # 关闭移动端上下文
            if context:
                await context.close()

            # 重新创建桌面上下文
            new_desktop_context, new_desktop_page = await browser_sim.create_context(
                browser_sim.browser,
                f"desktop_{self.args.browser}",
                storage_state=self.config.get("account.storage_state_path"),
            )

            self.logger.info("  ✓ 已切换回桌面上下文")
            return new_desktop_page

        StatusManager.update_progress(6, 8)
        return page  # 如果是 dry_run，返回原来的页面

    async def execute_daily_tasks(
        self,
        page: Any,
    ) -> Any:
        """执行日常任务"""
        state_monitor = self._get_state_monitor()
        browser_sim = self._get_browser_sim()

        if self.args.skip_daily_tasks:
            self.logger.info("\n[7/8] 跳过日常任务（--skip-daily-tasks）")
            StatusManager.update_progress(7, 8)
            return page  # 返回原来的页面

        self.logger.info("\n[7/8] 执行日常任务...")
        StatusManager.update_operation("执行日常任务")

        task_system_enabled = self.config.get("task_system.enabled", False)

        if task_system_enabled:
            try:
                from tasks import TaskManager

                task_manager = TaskManager(self.config)

                # 检查传入的 page 是否有效
                # 注意: execute_mobile_search 已经返回了有效的桌面页面
                # 不需要再创建新的上下文
                page_valid = False
                try:
                    await page.evaluate("() => document.readyState")
                    page_valid = True
                    self.logger.info("  使用现有桌面页面执行任务...")
                except Exception:
                    self.logger.warning("  传入的页面已失效，需要重建...")

                # 只有在页面无效时才创建新上下文
                if not page_valid:
                    if browser_sim and browser_sim.browser:
                        _, page = await browser_sim.create_context(
                            browser_sim.browser,
                            f"desktop_{self.args.browser}",
                            storage_state=self.config.get("account.storage_state_path"),
                        )
                    else:
                        await self._create_desktop_browser_if_needed(browser_sim)
                        _, page = await browser_sim.create_context(
                            browser_sim.browser,
                            f"desktop_{self.args.browser}",
                            storage_state=self.config.get("account.storage_state_path"),
                        )

                # 发现任务
                self.logger.info("  发现可用任务...")
                tasks = await task_manager.discover_tasks(page)

                if len(tasks) == 0:
                    self.logger.warning("  ⚠️ 未发现任何任务")
                    self._log_task_debug_info()
                else:
                    self.logger.info(f"  找到 {len(tasks)} 个任务")
                    completed_count = sum(1 for t in tasks if t.is_completed())
                    pending_count = len(tasks) - completed_count
                    self.logger.info(f"    待完成: {pending_count}, 已完成: {completed_count}")

                    if tasks:
                        points_detector = state_monitor.points_detector

                        points_before = getattr(state_monitor, "last_points", None) or getattr(
                            state_monitor, "initial_points", None
                        )

                        if points_before is None:
                            self.logger.info("  获取任务前积分...")
                            async with create_temp_page(page.context) as temp:
                                points_before = await points_detector.get_current_points(
                                    temp, skip_navigation=False
                                )

                            if points_before is None:
                                self.logger.warning("  ⚠️ 无法获取任务前积分，跳过积分验证")
                                points_before = None
                            else:
                                self.logger.info(f"  任务前积分: {points_before}")
                        else:
                            self.logger.info(f"  任务前积分 (缓存): {points_before}")

                        self.logger.info("  开始执行任务...")
                        report = await task_manager.execute_tasks(page, tasks)

                        async with create_temp_page(page.context) as temp:
                            points_after = await points_detector.get_current_points(
                                temp, skip_navigation=False
                            )

                        if points_after is None:
                            self.logger.warning("  ⚠️ 积分检测失败，使用报告值")
                            actual_points_gained = report.points_earned
                        elif points_before is None:
                            self.logger.warning("  ⚠️ 无任务前积分基线，使用报告值")
                            self.logger.info(f"  任务后积分: {points_after}")
                            actual_points_gained = report.points_earned
                        else:
                            self.logger.info(f"  任务后积分: {points_after}")
                            actual_points_gained = max(0, points_after - points_before)
                            if actual_points_gained != report.points_earned:
                                self.logger.warning(
                                    f"  ⚠️ 积分验证: 报告 {report.points_earned}, 实际 {actual_points_gained}"
                                )
                            if hasattr(state_monitor, "last_points"):
                                state_monitor.last_points = points_after

                        state_monitor.session_data["tasks_completed"] = report.completed
                        state_monitor.session_data["tasks_failed"] = report.failed
                        state_monitor.session_data["points_gained"] += actual_points_gained

                        self.logger.info("  ✓ 任务执行完成")
                        self.logger.info(
                            f"    完成: {report.completed}, 失败: {report.failed}, 跳过: {report.skipped}"
                        )
                        self.logger.info(f"    实际获得积分: +{actual_points_gained}")

            except ImportError as e:
                self.logger.warning(f"  ⚠ 任务系统模块导入失败: {e}")
                self.logger.warning("  请确保已安装所有依赖: pip install -r requirements.txt")
            except Exception as e:
                self.logger.error(f"  ✗ 任务执行失败: {e}")
                import traceback

                traceback.print_exc()
        else:
            if not task_system_enabled:
                self.logger.info("  ⚠ 任务系统未启用")
                self.logger.info("  提示: 在 config.yaml 中设置 task_system.enabled: true 来启用")
            else:
                self.logger.info("  [模拟] 将执行日常任务")

        StatusManager.update_progress(7, 8)
        return page

    def _log_task_debug_info(self) -> None:
        """记录任务调试信息"""
        self.logger.info("  可能原因:")
        self.logger.info("    1. 所有任务已完成")
        self.logger.info("    2. 页面结构已变化（选择器失效）")
        self.logger.info("    3. 未正确登录到奖励页面")
        if self.config.get("task_system.debug_mode", False):
            self.logger.info("  📊 诊断数据已保存到 logs/diagnostics/ 目录")

    # ============================================================
    # 依赖项获取方法
    # ============================================================

    def _get_account_manager(self) -> Any:
        """获取 AccountManager"""
        if self._account_manager is None:
            from account.manager import AccountManager

            self._account_manager = AccountManager(self.config)
        return self._account_manager

    def _get_search_engine(self) -> Any:
        """获取 SearchEngine"""
        if self._search_engine is None:
            from browser.anti_ban_module import AntiBanModule
            from search.search_engine import SearchEngine
            from search.search_term_generator import SearchTermGenerator
            from ui.real_time_status import StatusManager

            term_gen = SearchTermGenerator(self.config)
            anti_ban = AntiBanModule(self.config)
            state_monitor = self._get_state_monitor()
            self._search_engine = SearchEngine(
                self.config,
                term_gen,
                anti_ban,
                monitor=state_monitor,
                status_manager=StatusManager,
            )
        return self._search_engine

    def _get_state_monitor(self) -> Any:
        """获取 StateMonitor"""
        if self._state_monitor is None:
            from account.points_detector import PointsDetector
            from infrastructure.state_monitor import StateMonitor

            points_det = PointsDetector()
            self._state_monitor = StateMonitor(self.config, points_det)
        return self._state_monitor

    def _get_health_monitor(self) -> Any:
        """获取 HealthMonitor"""
        if self._health_monitor is None:
            from infrastructure.health_monitor import HealthMonitor

            self._health_monitor = HealthMonitor(self.config)
        return self._health_monitor

    def _get_browser_sim(self) -> Any:
        """获取 BrowserSimulator"""
        if self._browser_sim is None:
            raise RuntimeError("BrowserSimulator 未设置")
        return self._browser_sim

    async def _create_desktop_browser_if_needed(self, browser_sim: Any) -> None:
        """如果需要时创建桌面浏览器"""
        if not browser_sim.browser:
            self.logger.info("  创建桌面浏览器...")
            browser_sim.browser = await browser_sim.create_desktop_browser(self.args.browser)
            self.logger.info("  ✓ 桌面浏览器创建成功")
