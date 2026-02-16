"""
运行所有测试
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'=' * 70}")
    print(f"{description}")
    print("=" * 70)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent.parent,
        )

        print(result.stdout)

        if result.returncode == 0:
            print(f"✓ {description} - 通过")
            return True
        else:
            print(f"✗ {description} - 失败")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - 超时")
        return False
    except Exception as e:
        print(f"✗ {description} - 错误: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("MS Rewards Automator - 测试套件")
    print("=" * 70)

    results = {}

    # 1. 单元测试
    results["单元测试"] = run_command("pytest tests/ -v --tb=short", "运行单元测试")

    # 2. 属性测试
    results["属性测试"] = run_command("pytest tests/ -v --tb=short -m property", "运行属性测试")

    # 3. 环境检查
    results["环境检查"] = run_command("python tools/check_environment.py", "检查环境依赖")

    # 4. 配置验证
    results["配置验证"] = run_command(
        "python -c \"from src.infrastructure.config_manager import ConfigManager; c = ConfigManager('config.yaml'); print('配置文件有效')\"",
        "验证配置文件",
    )

    # 显示摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    print("\n" + "=" * 70)
    print(f"总计: {total} | 通过: {passed} | 失败: {failed}")
    print("=" * 70)

    if failed > 0:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
