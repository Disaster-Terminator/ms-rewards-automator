"""
SystemInitializer - 系统初始化器

负责所有核心组件的初始化工作。
遵循单一职责原则，将初始化逻辑从 main.py 中分离。
"""

import logging
from typing import Any

from account.manager import AccountManager
from account.points_detector import PointsDetector
from browser.anti_ban_module import AntiBanModule
from browser.simulator import BrowserSimulator
from infrastructure.error_handler import ErrorHandler
from infrastructure.health_monitor import HealthMonitor
from infrastructure.notificator import Notificator
from infrastructure.state_monitor import StateMonitor
from search.query_engine import QueryEngine
from search.search_engine import SearchEngine
from search.search_term_generator import SearchTermGenerator


class SystemInitializer:
    """
    系统初始化器

    负责创建和配置所有核心组件。
    """

    def __init__(self, config: Any, args: Any, logger: logging.Logger):
        """
        初始化初始化器

        Args:
            config: ConfigManager 实例
            args: 命令行参数
            logger: 日志记录器
        """
        self.config = config
        self.args = args
        self.logger = logger

    def initialize_components(self) -> tuple:
        """
        初始化所有核心组件

        Returns:
            (browser_sim, search_engine, account_mgr, state_monitor,
             error_handler, notificator, health_monitor)
        """
        # 应用命令行参数到配置
        self._apply_cli_args()

        # 创建反检测模块
        anti_ban = AntiBanModule(self.config)

        # 创建浏览器模拟器
        browser_sim = BrowserSimulator(self.config, anti_ban)

        # 创建搜索词生成器
        term_gen = SearchTermGenerator(self.config)

        # 创建积分检测器
        points_det = PointsDetector()

        # 创建账户管理器
        account_mgr = AccountManager(self.config)

        # 创建状态监控器
        state_monitor = StateMonitor(self.config, points_det)

        # 初始化 QueryEngine（如果启用）
        query_engine = self._init_query_engine()

        # 导入 StatusManager 用于进度显示
        from ui.real_time_status import StatusManager

        # 创建搜索引擎（传入 state_monitor 用于搜索计数）
        search_engine = SearchEngine(
            self.config,
            term_gen,
            anti_ban,
            monitor=state_monitor,
            query_engine=query_engine,
            status_manager=StatusManager,
        )

        # 创建错误处理器
        error_handler = ErrorHandler(self.config)

        # 创建通知器
        notificator = Notificator(self.config)

        # 创建健康监控器
        health_monitor = HealthMonitor(self.config)

        self.logger.info("  ✓ 完成")

        return (
            browser_sim,
            search_engine,
            account_mgr,
            state_monitor,
            error_handler,
            notificator,
            health_monitor,
        )

    def _apply_cli_args(self) -> None:
        """应用命令行参数到配置"""
        # 如果没有登录状态且没有明确指定 --headless，自动切换到有头模式
        import os

        storage_state_path = self.config.get("account.storage_state_path", "storage_state.json")
        has_login_state = os.path.exists(storage_state_path)

        if not has_login_state and not self.args.headless:
            self.logger.info("检测到首次运行（无登录状态），自动切换到有头模式以便登录")
            self.config.config["browser"]["headless"] = False

        if self.args.headless:
            self.config.config["browser"]["headless"] = True

    def _init_query_engine(self) -> QueryEngine | None:
        """初始化查询引擎"""
        if not self.config.get("query_engine.enabled", False):
            return None

        try:
            query_engine = QueryEngine(self.config)
            self.logger.info("  ✓ QueryEngine 已启用")
            return query_engine
        except Exception as e:
            self.logger.warning(f"  QueryEngine 初始化失败，使用传统生成器: {e}")
            return None
