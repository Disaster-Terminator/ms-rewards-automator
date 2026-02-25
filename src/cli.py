"""
RewardsCore CLI 入口
提供 rscore 命令行工具
"""

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime

from infrastructure.config_manager import ConfigManager
from infrastructure.config_validator import ConfigValidator
from infrastructure.logger import setup_logging
from infrastructure.ms_rewards_app import MSRewardsApp

logger = None

# 全局状态用于优雅关闭
_current_app: MSRewardsApp | None = None
_shutdown_requested = False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="rscore",
        description="RewardsCore - 自动化完成 Microsoft Rewards 任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  rscore                          # 生产环境（20次搜索，自动调度）
  rscore --headless               # 后台运行
  rscore --user                   # 用户模式（3次搜索，验证稳定性）
  rscore --dev                    # 开发模式（2次搜索，快速调试）
  rscore --browser chrome         # 使用 Chrome 浏览器
  rscore --test-notification      # 测试通知功能
        """,
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="开发模式（2次搜索，无拟人行为，最小等待时间，DEBUG日志）",
    )

    parser.add_argument(
        "--user",
        action="store_true",
        help="用户测试模式（3次搜索，保留拟人行为和防检测，DEBUG日志）",
    )

    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器窗口）")

    parser.add_argument(
        "--browser",
        choices=["edge", "chrome", "chromium"],
        default="chromium",
        help="浏览器类型 (默认: chromium，使用 Playwright 内置版本)",
    )

    parser.add_argument("--desktop-only", action="store_true", help="仅执行桌面搜索")

    parser.add_argument("--mobile-only", action="store_true", help="仅执行移动搜索")

    parser.add_argument("--skip-daily-tasks", action="store_true", help="跳过每日任务")

    parser.add_argument("--skip-search", action="store_true", help="跳过搜索任务，专注测试每日任务")

    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不执行实际操作")

    parser.add_argument("--test-notification", action="store_true", help="测试通知功能")

    parser.add_argument(
        "--diagnose",
        action="store_true",
        default=None,
        help="启用诊断模式",
    )

    parser.add_argument(
        "--no-diagnose",
        action="store_false",
        dest="diagnose",
        help="禁用诊断模式（覆盖 --dev/--user 的默认启用）",
    )

    parser.add_argument("--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)")

    return parser.parse_args()


async def test_notification_func(config):
    """测试通知功能"""
    global logger
    from infrastructure.notificator import Notificator

    notificator = Notificator(config)

    if not notificator.enabled:
        print("通知功能未启用，请先在配置文件中配置通知服务")
        return

    test_data = {
        "points_gained": 100,
        "current_points": 5000,
        "desktop_searches": 30,
        "mobile_searches": 20,
        "status": "测试",
        "alerts": [],
    }

    print("正在发送测试通知...")
    success = await notificator.send_daily_report(test_data)

    if success:
        print("✅ 测试通知发送成功！")
    else:
        print("❌ 测试通知发送失败，请检查配置")


def signal_handler(signum, frame):
    """信号处理器 - 触发优雅关闭"""
    global logger, _shutdown_requested

    if _shutdown_requested:
        # 第二次信号，强制退出
        if logger:
            logger.warning("收到第二次中断信号，强制退出")
        sys.exit(130)

    _shutdown_requested = True

    if logger:
        logger.info("\n收到中断信号，正在优雅关闭...")

    # 触发 KeyboardInterrupt 让 asyncio.run 正常退出
    # 这会让正在运行的协程收到异常并执行 finally 块
    raise KeyboardInterrupt("用户中断")


async def async_main():
    """异步主函数"""
    global logger, _current_app

    args = parse_arguments()

    log_level = "DEBUG" if args.dry_run or args.dev or args.user else "INFO"
    setup_logging(log_level=log_level, log_file="logs/automator.log", console=True)
    logger = logging.getLogger(__name__)

    try:
        config = ConfigManager(args.config, dev_mode=args.dev, user_mode=args.user)

        logger.info("验证配置文件...")
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate_config(config.config)

        if not is_valid:
            logger.error("配置验证失败:")
            for error in errors:
                logger.error(f"  - {error}")

            logger.info("尝试自动修复配置问题...")
            fixed_config = validator.fix_common_issues(config.config)
            config.config = fixed_config

            is_valid, errors, warnings = validator.validate_config(config.config)
            if is_valid:
                logger.info("✓ 配置问题已自动修复")
            else:
                logger.error("自动修复失败，请手动检查配置文件")
                return 1

        if warnings:
            logger.warning("配置警告:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        if args.dry_run:
            logger.info(validator.get_validation_report())

    except Exception:
        logger.exception("配置加载失败")
        return 1

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.test_notification:
        await test_notification_func(config)
        return 0

    # 三态逻辑：None=默认（dev/user启用），True=强制启用，False=强制禁用
    if args.diagnose is None:
        diagnose_enabled = args.dev or args.user
    else:
        diagnose_enabled = args.diagnose

    scheduler_enabled = config.get("scheduler.enabled", True)

    try:
        if scheduler_enabled:
            logger.info("启动调度模式...")
            from infrastructure.scheduler import TaskScheduler

            scheduler = TaskScheduler(config)

            async def scheduled_task():
                global _current_app
                _current_app = MSRewardsApp(config, args, diagnose=diagnose_enabled)
                return await _current_app.run()

            await scheduler.run_scheduled_task(scheduled_task, run_once_first=True)
        else:
            _current_app = MSRewardsApp(config, args, diagnose=diagnose_enabled)

            logger.info("=" * 70)
            logger.info("RewardsCore - 开始执行")
            logger.info("=" * 70)
            logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"浏览器: {args.browser}")
            logger.info(f"无头模式: {config.get('browser.headless', True)}")
            logger.info("=" * 70)

            from ui.real_time_status import StatusManager

            StatusManager.start(config)

            return await _current_app.run()

    except KeyboardInterrupt:
        logger.info("\n用户中断，正在清理资源...")
        # 确保清理资源
        if _current_app:
            try:
                await _current_app._cleanup()
            except Exception as e:
                logger.debug(f"清理过程中发生错误: {e}")
        return 130
    finally:
        _current_app = None


def main():
    """CLI 入口函数"""
    exit_code = asyncio.run(async_main())
    if isinstance(exit_code, int):
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
