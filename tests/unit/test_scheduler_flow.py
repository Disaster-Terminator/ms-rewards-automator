"""
调度器测试模块
验证调度器能否正常启动、等待、唤起任务
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config_manager import ConfigManager
from infrastructure.scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class SchedulerTestResult:
    def __init__(self):
        self.init_success = False
        self.task_executed = False
        self.scheduler_started = False
        self.wait_completed = False
        self.second_task_executed = False
        self.errors = []

    def to_dict(self):
        return {
            "init_success": self.init_success,
            "task_executed": self.task_executed,
            "scheduler_started": self.scheduler_started,
            "wait_completed": self.wait_completed,
            "second_task_executed": self.second_task_executed,
            "errors": self.errors,
            "passed": self.is_passed(),
        }

    def is_passed(self):
        return (
            self.init_success
            and self.task_executed
            and self.scheduler_started
            and self.wait_completed
            and self.second_task_executed
            and len(self.errors) == 0
        )


async def run_scheduler_test(test_delay_seconds: int = 5, config_path: str = "config.yaml"):
    """
    运行调度器测试

    Args:
        test_delay_seconds: 测试模式下调度延迟秒数
        config_path: 配置文件路径
    """
    result = SchedulerTestResult()

    print("\n" + "=" * 60)
    print("调度器测试模块")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"调度延迟: {test_delay_seconds} 秒")
    print("=" * 60)

    try:
        print("\n[1/5] 初始化配置...")
        config = ConfigManager(config_path)
        config.config["scheduler"]["enabled"] = True
        config.config["scheduler"]["test_delay_seconds"] = test_delay_seconds
        config.config["scheduler"]["run_once_on_start"] = True
        result.init_success = True
        print("      ✓ 配置初始化成功")

        execution_count = 0

        async def mock_task():
            nonlocal execution_count
            execution_count += 1
            print(f"\n      📋 任务执行 #{execution_count} - {datetime.now().strftime('%H:%M:%S')}")
            if execution_count == 1:
                result.task_executed = True
            elif execution_count == 2:
                result.second_task_executed = True
            await asyncio.sleep(0.5)

        print("\n[2/5] 创建调度器...")
        scheduler = TaskScheduler(config)
        result.scheduler_started = scheduler.enabled
        print(f"      ✓ 调度器已启用: {scheduler.enabled}")
        print(f"      ✓ 测试延迟: {test_delay_seconds} 秒")

        print("\n[3/5] 执行首次任务...")
        await mock_task()
        print("      ✓ 首次任务完成")

        print("\n[4/5] 等待调度器触发...")
        print(f"      等待 {test_delay_seconds} 秒后再次执行...")

        await scheduler.wait_until_next_run()
        result.wait_completed = True
        print("      ✓ 等待完成")

        print("\n[5/5] 执行第二次任务...")
        await mock_task()
        print("      ✓ 第二次任务完成")

    except Exception as e:
        result.errors.append(str(e))
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)

    def status_icon(x):
        return "✓" if x else "✗"

    print(f"  [{status_icon(result.init_success)}] 配置初始化")
    print(f"  [{status_icon(result.task_executed)}] 首次任务执行")
    print(f"  [{status_icon(result.scheduler_started)}] 调度器启动")
    print(f"  [{status_icon(result.wait_completed)}] 等待调度触发")
    print(f"  [{status_icon(result.second_task_executed)}] 第二次任务执行")

    if result.errors:
        print("\n错误信息:")
        for error in result.errors:
            print(f"  - {error}")

    print("\n" + "-" * 60)
    if result.is_passed():
        print("✅ 调度器测试通过")
    else:
        print("❌ 调度器测试失败")
    print("=" * 60)

    return result


async def run_quick_test():
    """快速测试（3秒延迟）"""
    return await run_scheduler_test(test_delay_seconds=3)


async def run_full_test():
    """完整测试（5秒延迟）"""
    return await run_scheduler_test(test_delay_seconds=5)


@pytest.fixture
def test_config_path():
    """测试配置文件路径"""
    return Path(__file__).parent.parent.parent / "config.example.yaml"


@pytest.mark.asyncio
async def test_scheduler_basic_flow(test_config_path):
    """测试调度器基本流程"""
    result = await run_scheduler_test(test_delay_seconds=2, config_path=str(test_config_path))
    assert result.is_passed(), f"调度器测试失败: {result.errors}"


@pytest.mark.asyncio
async def test_scheduler_config_defaults(test_config_path):
    """测试调度器默认配置"""
    config = ConfigManager(str(test_config_path))
    assert config.get("scheduler.enabled") is True
    assert config.get("scheduler.scheduled_hour") == 17
    assert config.get("scheduler.max_offset_minutes") == 45


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="调度器测试模块")
    parser.add_argument("--delay", type=int, default=5, help="调度延迟秒数（默认5秒）")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    result = asyncio.run(run_scheduler_test(args.delay, args.config))
    sys.exit(0 if result.is_passed() else 1)
