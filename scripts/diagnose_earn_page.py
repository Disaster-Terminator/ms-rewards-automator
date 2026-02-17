"""
诊断脚本：自动触发登录后分析earn页面结构
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright


async def diagnose():
    print("=" * 60)
    print("Earn页面结构诊断工具")
    print("=" * 60)

    async with async_playwright() as p:
        print("\n[0] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n[1] 导航到dashboard触发登录...")
        await page.goto("https://rewards.bing.com/dashboard", wait_until="domcontentloaded")

        print("\n" + "=" * 50)
        print("请在浏览器中完成登录")
        print("登录成功后会自动继续...")
        print("=" * 50)

        for _ in range(60):
            await asyncio.sleep(1)
            pages = context.pages
            if pages:
                current_page = pages[-1]
                url = current_page.url
                if "rewards.bing.com" in url and "login" not in url.lower():
                    print(f"\n检测到登录成功: {url}")
                    page = current_page
                    break
        else:
            print("超时，请手动确认后按Enter继续...")
            input()
            pages = context.pages
            if pages:
                page = pages[-1]

        print(f"\n当前URL: {page.url}")

        if "rewards.bing.com/earn" not in page.url:
            print("\n[2] 导航到earn页面...")
            await page.goto("https://rewards.bing.com/earn", wait_until="networkidle")
            await asyncio.sleep(3)
            print(f"当前URL: {page.url}")

        if "rewards.bing.com" not in page.url:
            print("错误: 无法到达earn页面")
            await browser.close()
            return

        print("\n[3] 分析页面板块...")
        try:
            sections = await page.evaluate("""
                () => {
                    const results = [];
                    const main = document.querySelector('main, [role="main"]') || document.body;
                    const allSections = main.querySelectorAll('section, [class*="section"], div[class*="flex"][class*="flex-col"]');

                    allSections.forEach((section, idx) => {
                        const id = section.id || `section_${idx}`;
                        const className = section.className || '';
                        const links = section.querySelectorAll('a[href]');

                        const linkInfo = [];
                        links.forEach(link => {
                            linkInfo.push({
                                href: link.getAttribute('href'),
                                text: (link.innerText || '').substring(0, 50).replace(/\\n/g, ' ')
                            });
                        });

                        if (linkInfo.length > 0) {
                            results.push({
                                id: id,
                                className: className.substring(0, 100),
                                linkCount: links.length,
                                links: linkInfo.slice(0, 5)
                            });
                        }
                    });

                    return results;
                }
            """)
        except Exception as e:
            print(f"分析失败: {e}")
            await browser.close()
            return

        print(f"    找到 {len(sections)} 个板块")
        for sec in sections:
            print(f"\n    板块 [{sec['id']}]: {sec['linkCount']} 个链接")
            for link in sec['links']:
                print(f"      → {link['href']}: {link['text'][:30]}")

        print("\n[4] 分析所有任务链接...")
        all_tasks = await page.evaluate("""
            () => {
                const tasks = [];
                const main = document.querySelector('main, [role="main"]') || document.body;
                const links = main.querySelectorAll('a[href]');

                links.forEach((link, idx) => {
                    const href = link.getAttribute('href') || '';
                    if (!href || href === '#' || href === '/earn' || href === '/dashboard') return;

                    const text = (link.innerText || '').replace(/\\n/g, ' ').trim();

                    const pointsEl = link.querySelector('.text-caption1Stronger');
                    const points = pointsEl ? pointsEl.innerText.trim() : null;

                    const classList = Array.from(link.classList || []);

                    const parent = link.parentElement;
                    const parentClass = parent ? Array.from(parent.classList || []).join(' ') : '';

                    tasks.push({
                        idx: idx,
                        href: href,
                        text: text.substring(0, 100),
                        points: points,
                        classes: classList.slice(0, 8),
                        parentClass: parentClass.substring(0, 150)
                    });
                });

                return tasks;
            }
        """)

        print(f"    找到 {len(all_tasks)} 个任务链接")
        for t in all_tasks[:15]:
            print(f"\n    [{t['idx']}] {t['text'][:50]}")
            print(f"        href: {t['href']}")
            print(f"        积分: {t['points']}")
            print(f"        类名: {t['classes'][:4]}")

        print("\n[5] 分析完成状态标记...")
        completion_info = await page.evaluate("""
            () => {
                const main = document.querySelector('main, [role="main"]') || document.body;
                const links = main.querySelectorAll('a[href]');

                const samples = [];
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    if (!href || href === '#' || href === '/earn') return;

                    const text = link.innerText || '';
                    const classList = Array.from(link.classList || []).join(' ');

                    const pointsEl = link.querySelector('.text-caption1Stronger');
                    const pointsClass = pointsEl ? Array.from(pointsEl.classList || []).join(' ') : '';

                    const circleEl = link.querySelector('[class*="rounded-full"], [class*="circle"]');
                    const circleClass = circleEl ? Array.from(circleEl.classList || []).join(' ') : '';

                    samples.push({
                        href: href.substring(0, 50),
                        text: text.substring(0, 40).replace(/\\n/g, ' '),
                        linkClass: classList.substring(0, 100),
                        pointsClass: pointsClass,
                        circleClass: circleClass
                    });
                });

                return samples.slice(0, 10);
            }
        """)

        print("    完成状态样本:")
        for s in completion_info:
            print(f"\n      文本: {s['text']}")
            print(f"      积分类名: {s['pointsClass']}")
            print(f"      圆圈类名: {s['circleClass']}")

        output_path = Path("logs/diagnostics/earn_structure.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "url": page.url,
                "sections": sections,
                "all_tasks": all_tasks,
                "completion_samples": completion_info
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[6] 结果已保存到: {output_path}")

        await browser.close()
        print("\n完成！")


if __name__ == "__main__":
    asyncio.run(diagnose())
