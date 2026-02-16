#!/usr/bin/env python3
"""
统一诊断工具 - MS Rewards Automator
整合所有诊断和验证功能
"""

import argparse
import sys
from importlib.util import find_spec
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_environment():
    """环境检查"""
    print("\n" + "=" * 50)
    print("环境检查")
    print("=" * 50)

    print(f"\n✓ Python版本: {sys.version}")

    try:
        import playwright

        print(f"✓ Playwright: {playwright.__version__}")
    except ImportError:
        print("✗ Playwright 未安装")
        return False

    if find_spec("yaml") is not None:
        print("✓ PyYAML 已安装")
    else:
        print("✗ PyYAML 未安装")
        return False

    config_path = project_root / "config.yaml"
    if config_path.exists():
        print(f"✓ 配置文件存在: {config_path}")
    else:
        print(f"✗ 配置文件不存在: {config_path}")
        return False

    print("\n✓ 环境检查通过")
    return True


def validate_config():
    """配置验证"""
    print("\n" + "=" * 50)
    print("配置验证")
    print("=" * 50)

    try:
        import yaml

        from src.infrastructure.config_validator import ConfigValidator

        config_path = project_root / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate_config(config)

        if is_valid:
            print("\n✓ 配置文件有效")
            if warnings:
                print("\n警告:")
                for warning in warnings:
                    print(f"  - {warning}")
            return True
        else:
            print("\n✗ 配置文件存在错误:")
            for error in errors:
                print(f"  - {error}")
            return False

    except Exception as e:
        print(f"\n✗ 配置验证失败: {e}")
        return False


def check_p0_config():
    """P0配置检查"""
    print("\n" + "=" * 50)
    print("P0模块配置检查")
    print("=" * 50)

    try:
        import yaml

        config_path = project_root / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        login_config = config.get("login", {})
        print("\n登录状态机:")
        print(f"  - 启用: {login_config.get('state_machine_enabled', False)}")
        print(f"  - 最大转换: {login_config.get('max_transitions', 20)}")

        task_config = config.get("task_system", {})
        print("\n任务系统:")
        print(f"  - 启用: {task_config.get('enabled', False)}")
        print(f"  - 跳过已完成: {task_config.get('skip_completed', True)}")

        query_config = config.get("query_engine", {})
        print("\n查询引擎:")
        print(f"  - 启用: {query_config.get('enabled', False)}")

        print("\n✓ P0配置检查完成")
        return True

    except Exception as e:
        print(f"\n✗ P0配置检查失败: {e}")
        return False


async def diagnose_task_discovery():
    """任务发现诊断"""
    print("\n" + "=" * 50)
    print("任务发现诊断")
    print("=" * 50)

    try:
        import yaml
        from playwright.async_api import async_playwright

        config_path = project_root / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        storage_state = config.get("account", {}).get("storage_state_path", "storage_state.json")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            if Path(storage_state).exists():
                context = await browser.new_context(storage_state=storage_state)
                print("✓ 使用已保存的会话状态")
            else:
                context = await browser.new_context()
                print("⚠ 未找到会话状态，使用新会话")

            page = await context.new_page()

            print("\n导航到 Rewards 页面...")
            await page.goto("https://rewards.microsoft.com/", wait_until="networkidle")
            await page.wait_for_load_state("domcontentloaded")

            selectors = ["mee-card", ".mee-card", '[class*="rewards-card"]', '[data-bi-id*="card"]']

            print("\n测试选择器:")
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: 找到 {len(elements)} 个元素")
                except Exception as e:
                    print(f"  {selector}: 错误 - {e}")

            await page.screenshot(path="debug_rewards_page.png")
            html = await page.content()
            with open("debug_rewards_page.html", "w", encoding="utf-8") as f:
                f.write(html)

            print("\n✓ 已保存:")
            print("  - debug_rewards_page.png")
            print("  - debug_rewards_page.html")

            print("\n按Enter继续...")
            input()

            await browser.close()

        return True

    except Exception as e:
        print(f"\n✗ 任务发现诊断失败: {e}")
        return False


async def verify_query_engine():
    """查询引擎验证"""
    print("\n" + "=" * 50)
    print("查询引擎验证")
    print("=" * 50)

    try:
        import yaml

        from src.search.query_engine import QueryEngine

        config_path = project_root / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        engine = QueryEngine(config)

        print("\n生成测试查询...")
        queries = await engine.generate_queries(count=10)

        print(f"\n✓ 成功生成 {len(queries)} 个查询:")
        for i, query in enumerate(queries[:5], 1):
            print(f"  {i}. {query}")

        if len(queries) > 5:
            print(f"  ... 还有 {len(queries) - 5} 个查询")

        return True

    except Exception as e:
        print(f"\n✗ 查询引擎验证失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MS Rewards Automator 诊断工具")
    parser.add_argument("--all", action="store_true", help="运行所有检查")
    parser.add_argument("--env", action="store_true", help="环境检查")
    parser.add_argument("--config", action="store_true", help="配置验证")
    parser.add_argument("--p0", action="store_true", help="P0配置检查")
    parser.add_argument("--tasks", action="store_true", help="任务发现诊断")
    parser.add_argument("--query", action="store_true", help="查询引擎验证")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    print("\n" + "=" * 50)
    print("MS Rewards Automator - 统一诊断工具")
    print("=" * 50)

    results = []

    if args.all or args.env:
        results.append(("环境检查", check_environment()))

    if args.all or args.config:
        results.append(("配置验证", validate_config()))

    if args.all or args.p0:
        results.append(("P0配置", check_p0_config()))

    if args.all or args.tasks:
        import asyncio

        result = asyncio.run(diagnose_task_discovery())
        results.append(("任务发现", result))

    if args.all or args.query:
        import asyncio

        result = asyncio.run(verify_query_engine())
        results.append(("查询引擎", result))

    print("\n" + "=" * 50)
    print("诊断总结")
    print("=" * 50)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n✓ 所有检查通过")
        sys.exit(0)
    else:
        print("\n✗ 部分检查失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
