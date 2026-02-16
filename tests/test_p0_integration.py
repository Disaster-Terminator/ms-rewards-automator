"""
P0模块集成测试脚本
测试Login State Machine、Task System和Query Engine的集成
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.logger import setup_logging


async def test_query_engine():
    """测试Query Engine"""
    print("\n" + "=" * 70)
    print("测试 Query Engine")
    print("=" * 70)

    try:
        from search.query_engine import QueryEngine

        config = ConfigManager("config.yaml")
        query_engine = QueryEngine(config)

        print("✓ QueryEngine 初始化成功")

        # 测试获取查询
        print("\n获取10个查询...")
        queries = await query_engine.get_queries(10)

        print(f"✓ 获取到 {len(queries)} 个查询:")
        for i, query in enumerate(queries[:5], 1):
            print(f"  {i}. {query}")
        if len(queries) > 5:
            print(f"  ... 还有 {len(queries) - 5} 个")

        # 测试缓存
        print("\n测试缓存...")
        queries2 = await query_engine.get_queries(5)
        print(f"✓ 再次获取 {len(queries2)} 个查询（应该从缓存获取）")

        return True

    except Exception as e:
        print(f"✗ Query Engine 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_login_state_machine():
    """测试Login State Machine"""
    print("\n" + "=" * 70)
    print("测试 Login State Machine")
    print("=" * 70)

    try:
        from login.login_state_machine import LoginState, LoginStateMachine

        config = ConfigManager("config.yaml")
        logger = logging.getLogger(__name__)

        state_machine = LoginStateMachine(config, logger)

        print("✓ LoginStateMachine 初始化成功")
        print(f"  最大转换次数: {state_machine.max_transitions}")
        print(f"  转换超时: {state_machine.transition_timeout}秒")

        # 检查处理器注册
        print("\n已注册的状态处理器:")
        for state in LoginState:
            if state in state_machine.handlers:
                handler = state_machine.handlers[state]
                print(f"  ✓ {state.value}: {handler.__class__.__name__}")
            else:
                print(f"  ✗ {state.value}: 未注册")

        return True

    except Exception as e:
        print(f"✗ Login State Machine 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_task_system():
    """测试Task System"""
    print("\n" + "=" * 70)
    print("测试 Task System")
    print("=" * 70)

    try:
        from tasks import TaskManager, TaskParser

        config = ConfigManager("config.yaml")
        task_manager = TaskManager(config)

        print("✓ TaskManager 初始化成功")
        print(f"  已注册的任务类型: {len(task_manager.task_registry)}")

        for task_type, task_class in task_manager.task_registry.items():
            print(f"    - {task_type}: {task_class.__name__}")

        # 测试TaskParser
        TaskParser()
        print("\n✓ TaskParser 初始化成功")

        return True

    except Exception as e:
        print(f"✗ Task System 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_config():
    """测试配置文件"""
    print("\n" + "=" * 70)
    print("测试配置文件")
    print("=" * 70)

    try:
        config = ConfigManager("config.yaml")

        # 检查P0模块配置
        print("\n查询引擎配置:")
        print(f"  启用: {config.get('query_engine.enabled', False)}")
        print(f"  缓存TTL: {config.get('query_engine.cache_ttl', 3600)}秒")

        print("\n登录状态机配置:")
        print(f"  启用: {config.get('login.state_machine_enabled', True)}")
        print(f"  最大转换: {config.get('login.max_transitions', 20)}")

        print("\n任务系统配置:")
        print(f"  启用: {config.get('task_system.enabled', False)}")
        print(
            f"  延迟范围: {config.get('task_system.min_delay', 2)}-{config.get('task_system.max_delay', 5)}秒"
        )

        return True

    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 70)
    print("P0模块集成测试")
    print("=" * 70)

    # 设置日志
    setup_logging(log_level="INFO", console=True)

    results = {}

    # 测试配置
    results["config"] = await test_config()

    # 测试Query Engine
    results["query_engine"] = await test_query_engine()

    # 测试Login State Machine
    results["login_state_machine"] = await test_login_state_machine()

    # 测试Task System
    results["task_system"] = await test_task_system()

    # 显示总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    for module, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{module:25s}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有测试通过！P0模块已正确集成")
        print("\n下一步:")
        print("1. 启用模块: 编辑 config.yaml，设置:")
        print("   - query_engine.enabled: true")
        print("   - task_system.enabled: true")
        print("2. 运行主程序: python main.py")
        print("3. 或快速测试: python main.py --mode fast --desktop-only")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
