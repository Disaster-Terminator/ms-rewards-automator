"""
MS Rewards Automator - 主程序入口
支持命令行参数和调度模式
"""

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config_manager import ConfigManager
from infrastructure.config_validator import ConfigValidator
from infrastructure.logger import setup_logging

# 导入新的架构类
from infrastructure.ms_rewards_app import MSRewardsApp

logger = None
browser_sim = None
notificator = None


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MS Rewards Automator - 自动化完成 Microsoft Rewards 任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                          # 生产环境（30+20搜索，自动调度）
  python main.py --headless               # 后台运行
  python main.py --user                   # 用户模式（3+3搜索，验证稳定性）
  python main.py --dev                    # 开发模式（2+2搜索，快速调试）
  python main.py --browser chrome         # 使用 Chrome 浏览器
  python main.py --test-notification      # 测试通知功能
        """,
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="开发模式（2+2搜索，无拟人行为，最小等待时间，DEBUG日志）",
    )

    parser.add_argument(
        "--user",
        action="store_true",
        help="用户模式（3+3搜索，保留拟人行为和防检测，INFO日志）",
    )

    # 浏览器选项
    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器窗口）")

    parser.add_argument(
        "--browser",
        choices=["edge", "chrome", "chromium"],
        default="chromium",
        help="浏览器类型 (默认: chromium，使用 Playwright 内置版本)",
    )

    # 搜索选项
    parser.add_argument("--desktop-only", action="store_true", help="仅执行桌面搜索")

    parser.add_argument("--mobile-only", action="store_true", help="仅执行移动搜索")

    # 任务选项
    parser.add_argument("--skip-daily-tasks", action="store_true", help="跳过每日任务")

    # 测试选项
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不执行实际操作")

    parser.add_argument("--test-notification", action="store_true", help="测试通知功能")

    parser.add_argument(
        "--autonomous-test", action="store_true", help="运行自主测试框架（无头模式，自动问题发现）"
    )

    parser.add_argument(
        "--test-type",
        choices=["login", "bing_access", "search", "points", "full"],
        default="full",
        help="自主测试类型 (默认: full)",
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="自主测试快速模式：仅在 --autonomous-test 下生效，缩短测试检查间隔（不影响搜索等待/slow_mo）",
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


async def run_autonomous_test(args):
    """运行自主测试框架"""
    sys.path.insert(0, str(Path(__file__).parent))

    from tests.autonomous.autonomous_test_runner import AutonomousTestRunner, TestConfig

    print("\n" + "=" * 70)
    print("MS Rewards Automator - 自主测试框架")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试类型: {args.test_type}")
    print("=" * 70)

    test_config = TestConfig(
        headless=True,
        auto_screenshot=True,
        screenshot_on_error=True,
        stop_on_critical=True,
        max_retries=3,
        page_timeout=30000,
        inspection_interval=3 if args.quick_test else 5,
    )

    runner = AutonomousTestRunner(config_path=args.config, test_config=test_config)

    results = {"session_id": runner.screenshot_manager.session_id, "tests": {}, "reports": {}}

    try:
        if not await runner.initialize():
            print("❌ 初始化失败")
            return 1

        if not await runner.create_browser():
            print("❌ 创建浏览器失败")
            return 1

        storage_state = runner.config.get("account.storage_state_path")
        if not await runner.create_context(storage_state):
            print("❌ 创建上下文失败")
            return 1

        test_map = {
            "login": ("登录状态检测", runner._test_login_status),
            "bing_access": ("Bing访问测试", runner._test_bing_access),
            "search": ("搜索功能测试", runner._test_search_function),
            "points": ("积分检测测试", runner._test_points_detection),
        }

        if args.test_type == "full":
            for test_key, (test_name, test_func) in test_map.items():
                results["tests"][test_key] = await runner.run_test(test_name, test_func)
        else:
            test_name, test_func = test_map[args.test_type]
            results["tests"][args.test_type] = await runner.run_test(test_name, test_func)

    except KeyboardInterrupt:
        print("\n用户中断测试")
        results["interrupted"] = True

    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        results["error"] = str(e)

    finally:
        await runner.cleanup()

    results["reports"] = runner.generate_reports()

    print("\n" + "=" * 70)
    print("测试结果摘要")
    print("=" * 70)

    passed = sum(1 for v in results["tests"].values() if v)
    total = len(results["tests"])

    for test_name, test_result in results["tests"].items():
        status = "✅ 通过" if test_result else "❌ 失败"
        print(f"  {test_name}: {status}")

    print("\n" + "-" * 70)
    print(f"总计: {total} | 通过: {passed} | 失败: {total - passed}")

    if results.get("reports"):
        print("\n报告文件:")
        for report_type, path in results["reports"].items():
            print(f"  {report_type}: {path}")

    print("=" * 70)

    return 0 if passed == total else 1


def signal_handler(signum, frame):
    """信号处理器"""
    global browser_sim
    logger.info("\n收到中断信号，正在清理...")
    if browser_sim:
        asyncio.create_task(browser_sim.close())
    sys.exit(0)


async def main():
    """主函数"""
    global logger

    args = parse_arguments()

    log_level = "DEBUG" if args.dry_run or args.dev else "INFO"
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
            print(validator.get_validation_report())

    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.test_notification:
        await test_notification_func(config)
        return

    if args.autonomous_test:
        return await run_autonomous_test(args)

    scheduler_enabled = config.get("scheduler.enabled", True)

    if scheduler_enabled:
        logger.info("启动调度模式...")
        from infrastructure.scheduler import TaskScheduler

        scheduler = TaskScheduler(config)

        async def scheduled_task():
            app = MSRewardsApp(config, args)
            await app.run()

        await scheduler.run_scheduled_task(scheduled_task, run_once_first=True)
    else:
        app = MSRewardsApp(config, args)

        logger.info("=" * 70)
        logger.info("MS Rewards Automator - 开始执行")
        logger.info("=" * 70)
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"浏览器: {args.browser}")
        logger.info(f"无头模式: {config.get('browser.headless', True)}")
        logger.info("=" * 70)

        if not config.get("browser.headless", True):
            from ui.real_time_status import StatusManager

            StatusManager.start(config)

        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
