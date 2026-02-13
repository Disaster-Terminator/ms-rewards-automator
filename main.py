"""
MS Rewards Automator - 主程序入口
支持命令行参数和调度模式
"""

import asyncio
import sys
import os
import signal
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config_manager import ConfigManager
from infrastructure.config_validator import ConfigValidator
from infrastructure.logger import setup_logging
from infrastructure.log_rotation import LogRotation

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
  python main.py                          # 立即执行一次任务
  python main.py --headless               # 无头模式执行
  python main.py --mode fast              # 快速模式（减少等待时间）
  python main.py --schedule               # 调度模式（每天自动执行）
  python main.py --schedule --schedule-now # 调度模式（立即执行一次后进入调度）
  python main.py --desktop-only           # 仅执行桌面搜索
  python main.py --mobile-only            # 仅执行移动搜索
  python main.py --test-notification      # 测试通知功能
        """
    )

    # 执行模式
    parser.add_argument(
        "--mode",
        choices=["normal", "fast", "slow"],
        default="normal",
        help="执行模式: normal(正常), fast(快速), slow(慢速)"
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="开发模式（快速配置：3次搜索，2秒间隔，DEBUG日志）"
    )

    # 浏览器选项
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式（不显示浏览器窗口）"
    )

    parser.add_argument(
        "--browser",
        choices=["edge", "chrome", "chromium"],
        default="chromium",
        help="浏览器类型 (默认: chromium，使用 Playwright 内置版本)"
    )

    # 搜索选项
    parser.add_argument(
        "--desktop-only",
        action="store_true",
        help="仅执行桌面搜索"
    )

    parser.add_argument(
        "--mobile-only",
        action="store_true",
        help="仅执行移动搜索"
    )

    # 任务选项
    parser.add_argument(
        "--skip-daily-tasks",
        action="store_true",
        help="跳过每日任务"
    )

    # 测试选项
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不执行实际操作"
    )

    parser.add_argument(
        "--test-notification",
        action="store_true",
        help="测试通知功能"
    )

    # 调度选项
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="启用调度模式"
    )

    parser.add_argument(
        "--schedule-now",
        action="store_true",
        help="立即执行一次后进入调度"
    )

    # 配置文件
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )

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
        "alerts": []
    }

    print("正在发送测试通知...")
    success = await notificator.send_daily_report(test_data)

    if success:
        print("✅ 测试通知发送成功！")
    else:
        print("❌ 测试通知发送失败，请检查配置")


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
    log_level = "DEBUG" if args.dry_run or args.dev else "INFO"
    setup_logging(log_level=log_level, log_file="logs/automator.log", console=True)
    logger = logging.getLogger(__name__)

    # 加载配置
    try:
        config = ConfigManager(args.config, dev_mode=args.dev)

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

    # 调度模式
    if args.schedule:
        logger.info("启动调度模式...")
        from infrastructure.scheduler import TaskScheduler
        scheduler = TaskScheduler(config)

        # 定义调度任务
        async def scheduled_task():
            app = MSRewardsApp(config, args)
            await app.run()

        # 如果指定了 --schedule-now，立即执行一次
        if args.schedule_now:
            logger.info("\n⚡ 立即执行一次任务（测试模式）...")
            logger.info("=" * 70)
            await scheduled_task()
            logger.info("=" * 70)
            logger.info("✓ 立即执行完成，现在进入正常调度模式\n")

        await scheduler.run_scheduled_task(scheduled_task)
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
