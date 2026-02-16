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
  python main.py                          # 生产环境（完整配置，30+20搜索）
  python main.py --usermode               # 测试模式（3+3搜索，验证稳定性）
  python main.py --dev                    # 开发模式（2+2搜索，快速迭代）
  python main.py --headless               # 无头模式执行
  python main.py --mode fast              # 快速模式（减少等待时间）
  python main.py --schedule               # 调度模式（每天自动执行）
  python main.py --schedule --schedule-now # 调度模式（立即执行一次后进入调度）
  python main.py --desktop-only           # 仅执行桌面搜索
  python main.py --mobile-only            # 仅执行移动搜索
  python main.py --test-notification      # 测试通知功能
  python main.py --autonomous-test        # 运行自主测试框架
  python main.py --autonomous-test --test-type login  # 仅测试登录状态
  python main.py --autonomous-test --quick-test       # 快速测试模式
        """,
    )

    # 执行模式
    parser.add_argument(
        "--mode",
        choices=["normal", "fast", "slow"],
        default="normal",
        help="执行模式: normal(正常), fast(快速), slow(慢速)",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="开发模式（2+2搜索，无拟人行为，最小等待时间，DEBUG日志）",
    )

    parser.add_argument(
        "--usermode",
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

    parser.add_argument("--quick-test", action="store_true", help="快速测试模式（减少等待时间）")

    # 调度选项
    parser.add_argument("--schedule", action="store_true", help="启用调度模式")

    parser.add_argument("--schedule-now", action="store_true", help="立即执行一次后进入调度")

    parser.add_argument(
        "--no-schedule",
        action="store_true",
        help="仅执行一次，不进入调度（覆盖配置中的调度器启用）",
    )

    parser.add_argument(
        "--schedule-only", action="store_true", help="跳过首次执行，直接进入调度模式"
    )

    # 配置文件
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

    # 解析参数
    args = parse_arguments()

    # 初始化日志
    # dev模式: DEBUG日志, 快速配置
    # usermode模式: INFO日志, 完整配置（模拟真实使用）
    # 默认: INFO日志, 完整配置
    log_level = "DEBUG" if args.dry_run or args.dev else "INFO"
    setup_logging(log_level=log_level, log_file="logs/automator.log", console=True)
    logger = logging.getLogger(__name__)

    # 加载配置
    # dev模式: 2+2搜索，无拟人行为，最小等待时间
    # usermode模式: 3+3搜索，保留拟人行为和防检测
    try:
        config = ConfigManager(args.config, dev_mode=args.dev, user_mode=args.usermode)

        # 验证配置
        logger.info("验证配置文件...")
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate_config(config.config)

        if not is_valid:
            logger.error("配置验证失败:")
            for error in errors:
                logger.error(f"  - {error}")

            # 尝试自动修复
            logger.info("尝试自动修复配置问题...")
            fixed_config = validator.fix_common_issues(config.config)
            config.config = fixed_config

            # 重新验证
            is_valid, errors, warnings = validator.validate_config(config.config)
            if is_valid:
                logger.info("✓ 配置问题已自动修复")
            else:
                logger.error("自动修复失败，请手动检查配置文件")
                return 1

        # 显示警告
        if warnings:
            logger.warning("配置警告:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        # 显示验证报告（仅在调试模式下）
        if args.dry_run:
            print(validator.get_validation_report())

    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        sys.exit(1)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 测试通知
    if args.test_notification:
        await test_notification_func(config)
        return

    # 自主测试模式
    if args.autonomous_test:
        return await run_autonomous_test(args)

    # 判断调度器是否启用
    scheduler_enabled = config.get("scheduler.enabled", False)

    # --no-schedule 参数覆盖配置
    if args.no_schedule:
        scheduler_enabled = False
        logger.info("⚡ --no-schedule 参数已设置，跳过调度模式")

    # 调度模式
    if scheduler_enabled:
        logger.info("启动调度模式...")
        from infrastructure.scheduler import TaskScheduler

        scheduler = TaskScheduler(config)

        # 定义调度任务
        async def scheduled_task():
            app = MSRewardsApp(config, args)
            await app.run()

        # --schedule-only 跳过首次执行，直接进入调度
        run_once_first = not args.schedule_only
        if args.schedule_only:
            logger.info("⚡ --schedule-only 参数已设置，跳过首次执行，直接进入调度")

        # 兼容旧的 --schedule-now 参数（等同于默认行为）
        if args.schedule_now:
            logger.info("⚡ --schedule-now 参数已设置（现在这是默认行为）")

        await scheduler.run_scheduled_task(scheduled_task, run_once_first=run_once_first)
    else:
        # 立即执行 - 使用新的架构
        app = MSRewardsApp(config, args)

        # 输出基本信息
        logger.info("=" * 70)
        logger.info("MS Rewards Automator - 开始执行")
        logger.info("=" * 70)
        logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"执行模式: {args.mode}")
        logger.info(f"浏览器: {args.browser}")
        logger.info(f"无头模式: {config.get('browser.headless', True)}")
        logger.info("=" * 70)

        # 启动实时状态显示
        if not config.get("browser.headless", True):
            from ui.real_time_status import StatusManager

            StatusManager.start(config)

        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
