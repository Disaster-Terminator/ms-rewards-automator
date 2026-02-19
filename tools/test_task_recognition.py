"""
测试任务识别脚本
验证task_parser能否正确识别earn页面的任务
"""

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.session_helpers import create_session_browser, wait_for_login  # noqa: E402


async def test_task_recognition():
    print("=" * 60)
    print("任务识别测试")
    print("=" * 60)

    async with async_playwright() as p:
        print("\n[0] 启动浏览器...")
        browser, context, page, has_session = await create_session_browser(p)

        if has_session:
            print("  ✓ 使用已保存的会话状态")
        else:
            print("  ⚠ 未找到会话状态，使用新会话（请手动登录）")

        print("\n[1] 导航到earn页面...")
        await page.goto("https://rewards.bing.com/earn", wait_until="domcontentloaded")

        await wait_for_login(page, context, has_session)

        if "rewards.bing.com/earn" not in page.url:
            print("\n[2] 导航到earn页面...")
            await page.goto("https://rewards.bing.com/earn", wait_until="networkidle")
            await asyncio.sleep(3)

        print(f"\n当前URL: {page.url}")

        print("\n[3] 测试task_parser解析...")
        from src.tasks.task_parser import TaskParser

        parser = TaskParser()
        tasks = await parser.discover_tasks(page)

        print(f"\n发现 {len(tasks)} 个任务:")
        print("-" * 50)

        completed_count = 0
        incomplete_count = 0
        total_points = 0

        for i, task in enumerate(tasks):
            status = "✅ 已完成" if task.is_completed else "⭕ 未完成"
            print(f"\n[{i + 1}] {task.title}")
            print(f"    类型: {task.task_type} | 积分: {task.points} | {status}")
            print(f"    URL: {task.destination_url[:60]}...")

            if task.is_completed:
                completed_count += 1
            else:
                incomplete_count += 1
            total_points += task.points

        print("\n" + "=" * 50)
        print("统计:")
        print(f"  总任务数: {len(tasks)}")
        print(f"  已完成: {completed_count}")
        print(f"  未完成: {incomplete_count}")
        print(f"  总积分: {total_points}")
        print("=" * 50)

        output_path = Path("logs/diagnostics/task_recognition_test.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_tasks": len(tasks),
                    "completed": completed_count,
                    "incomplete": incomplete_count,
                    "total_points": total_points,
                    "tasks": [
                        {
                            "title": t.title,
                            "type": t.task_type,
                            "points": t.points,
                            "completed": t.is_completed,
                            "url": t.destination_url,
                        }
                        for t in tasks
                    ],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n结果已保存到: {output_path}")

        await browser.close()
        print("\n完成！")


if __name__ == "__main__":
    asyncio.run(test_task_recognition())
