"""
自主测试入口脚本
支持命令行参数，可独立运行完整测试流程
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_project_root))

from tests.autonomous.autonomous_test_runner import AutonomousTestRunner, TestConfig  # noqa: E402


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """设置日志"""
    import io

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = []

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    handlers.append(console_handler)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MS Rewards Automator - 自主测试框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_autonomous_tests.py                           # 运行完整测试套件
  python run_autonomous_tests.py --integrated              # 集成测试（开发模式，快速调试）
  python run_autonomous_tests.py --integrated --user-mode  # 集成测试（用户模式，启用防检测）
  python run_autonomous_tests.py --headless                # 无头模式运行
  python run_autonomous_tests.py --quick                   # 快速测试模式
  python run_autonomous_tests.py --test login              # 仅运行登录测试
  python run_autonomous_tests.py --no-screenshot           # 禁用自动截图
  python run_autonomous_tests.py --report-only             # 仅生成报告

测试类型:
  login        - 登录状态检测
  bing_access  - Bing访问测试
  search       - 搜索功能测试
  points       - 积分检测测试
  full         - 完整测试套件（默认）
  integrated   - 集成测试（复用 MSRewardsApp）

测试模式:
  --dev        - 开发模式：快速调试，禁用防检测，2+2搜索
  --user-mode  - 用户模式：鲁棒性测试，启用防检测，3+3搜索
        """,
    )

    parser.add_argument("--config", default="config.yaml", help="配置文件路径 (默认: config.yaml)")

    parser.add_argument(
        "--headless", action="store_true", default=True, help="无头模式运行 (默认: True)"
    )

    parser.add_argument("--no-headless", action="store_true", help="显示浏览器窗口")

    parser.add_argument(
        "--test",
        choices=["login", "bing_access", "search", "points", "full", "integrated"],
        default="full",
        help="要运行的测试类型 (默认: full)",
    )

    parser.add_argument(
        "--integrated", action="store_true", help="运行集成测试（复用 MSRewardsApp 执行完整流程）"
    )

    parser.add_argument(
        "--user-mode",
        action="store_true",
        help="用户模式测试（启用防检测，模拟真实环境，有头模式）",
    )

    parser.add_argument(
        "--dev", action="store_true", help="开发模式测试（快速调试，禁用防检测，有头模式）"
    )

    parser.add_argument("--quick", action="store_true", help="快速测试模式（减少等待时间）")

    parser.add_argument("--no-screenshot", action="store_true", help="禁用自动截图")

    parser.add_argument(
        "--screenshot-on-error",
        action="store_true",
        default=True,
        help="仅在错误时截图 (默认: True)",
    )

    parser.add_argument(
        "--stop-on-critical",
        action="store_true",
        default=True,
        help="发现严重问题时停止测试 (默认: True)",
    )

    parser.add_argument("--max-retries", type=int, default=3, help="最大重试次数 (默认: 3)")

    parser.add_argument(
        "--timeout", type=int, default=30000, help="页面超时时间(毫秒) (默认: 30000)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )

    parser.add_argument("--log-file", default=None, help="日志文件路径")

    parser.add_argument("--report-only", action="store_true", help="仅生成报告（不运行测试）")

    parser.add_argument(
        "--output-dir", default="logs/test_reports", help="报告输出目录 (默认: logs/test_reports)"
    )

    parser.add_argument("--cleanup", action="store_true", help="清理旧的测试数据（保留最近5次）")

    parser.add_argument("--keep-reports", type=int, default=5, help="保留最近N次测试报告 (默认: 5)")

    return parser.parse_args()


def cleanup_old_test_data(keep_count: int = 5):
    """清理旧的测试数据"""
    import shutil

    base_dir = Path("logs")
    dirs_to_clean = ["test_reports", "screenshots"]

    cleaned = 0

    for dir_name in dirs_to_clean:
        target_dir = base_dir / dir_name
        if not target_dir.exists():
            continue

        subdirs = sorted(
            [d for d in target_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for old_dir in subdirs[keep_count:]:
            try:
                shutil.rmtree(old_dir)
                cleaned += 1
                print(f"已清理: {old_dir}")
            except Exception as e:
                print(f"清理失败 {old_dir}: {e}")

    files_to_clean = ["diagnosis_report.json"]
    for file_name in files_to_clean:
        file_path = base_dir / file_name
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

    if cleaned > 0:
        print(f"\n已清理 {cleaned} 个旧测试目录")
    else:
        print("\n无需清理")

    return cleaned


async def run_single_test(runner: AutonomousTestRunner, test_type: str) -> bool:
    """运行单个测试"""
    test_map = {
        "login": ("登录状态检测", runner._test_login_status),
        "bing_access": ("Bing访问测试", runner._test_bing_access),
        "search": ("搜索功能测试", runner._test_search_function),
        "points": ("积分检测测试", runner._test_points_detection),
    }

    if test_type in test_map:
        name, test_func = test_map[test_type]
        return await runner.run_test(name, test_func)

    return False


async def main():
    """主函数"""
    args = parse_arguments()

    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)

    if args.cleanup:
        print("\n清理旧的测试数据...")
        cleanup_old_test_data(args.keep_reports)
        print("")

    print("\n" + "=" * 70)
    print("MS Rewards Automator - 自主测试框架")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"配置文件: {args.config}")
    print(f"测试类型: {args.test}")

    if args.integrated:
        mode_str = "用户模式（启用防检测）" if args.user_mode else "开发模式（快速调试）"
        print(f"测试模式: 集成测试 - {mode_str}")
    else:
        print(f"无头模式: {not args.no_headless}")

    print("=" * 70)

    if args.integrated or args.test == "integrated":
        return await run_integrated_test_mode(args)

    test_config = TestConfig(
        headless=not args.no_headless,
        auto_screenshot=not args.no_screenshot,
        screenshot_on_error=args.screenshot_on_error,
        stop_on_critical=args.stop_on_critical,
        max_retries=args.max_retries,
        page_timeout=args.timeout,
        inspection_interval=3 if args.quick else 5,
    )

    runner = AutonomousTestRunner(config_path=args.config, test_config=test_config)

    runner.reporter.output_dir = Path(args.output_dir)

    results = {"session_id": runner.screenshot_manager.session_id, "tests": {}, "reports": {}}

    try:
        if not await runner.initialize():
            logger.error("初始化失败")
            return 1

        if not await runner.create_browser():
            logger.error("创建浏览器失败")
            return 1

        storage_state = runner.config.get("account.storage_state_path")
        if not await runner.create_context(storage_state):
            logger.error("创建上下文失败")
            return 1

        if args.test == "full":
            results["tests"]["login"] = await runner.run_test(
                "登录状态检测", runner._test_login_status
            )

            results["tests"]["bing_access"] = await runner.run_test(
                "Bing访问测试", runner._test_bing_access
            )

            results["tests"]["search_function"] = await runner.run_test(
                "搜索功能测试", runner._test_search_function
            )

            results["tests"]["points_detection"] = await runner.run_test(
                "积分检测测试", runner._test_points_detection
            )
        else:
            results["tests"][args.test] = await run_single_test(runner, args.test)

    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
        results["interrupted"] = True

    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        results["error"] = str(e)

    finally:
        await runner.cleanup()

    results["reports"] = runner.generate_reports()

    print_results(results)

    passed = sum(1 for v in results["tests"].values() if v)
    total = len(results["tests"])

    if passed == total and total > 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请查看报告了解详情")
        return 1


async def run_integrated_test_mode(args):
    """运行集成测试模式"""
    from tests.autonomous.integrated_test_runner import IntegratedTestRunner

    user_mode = args.user_mode
    mode_str = "用户模式（启用防检测）" if user_mode else "开发模式（快速调试）"

    print(f"\n🚀 运行集成测试 - {mode_str}")
    print("-" * 70)

    runner = IntegratedTestRunner(config_path=args.config, user_mode=user_mode)

    try:
        results = await runner.run_full_test()
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print_results(results)

    if results["tests"].get("full_test"):
        print("\n✅ 集成测试通过！")
        return 0
    else:
        print("\n⚠️ 集成测试失败，请查看报告了解详情")
        return 1


def print_results(results: dict[str, Any]):
    """打印测试结果"""
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


async def run_integrated_test(
    config_path: str = "config.yaml", user_mode: bool = False
) -> dict[str, Any]:
    """运行集成测试"""
    from tests.autonomous.integrated_test_runner import IntegratedTestRunner

    runner = IntegratedTestRunner(config_path, user_mode=user_mode)
    return await runner.run_full_test()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
