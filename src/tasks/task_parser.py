"""
Task Parser for extracting task information from Microsoft Rewards dashboard
Supports the new React-based rewards.bing.com dashboard (2025+)
"""

import logging

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from tasks.task_base import TaskMetadata

SKIP_HREFS = [
    "/earn",
    "/dashboard",
    "/about",
    "/refer",
    "/",
    "/orderhistory",
    "/faq",
    "rewards.bing.com/referandearn",
    "rewards.bing.com/redeem",
    "support.microsoft.com",
    "x.com",
    "xbox.com",
    "microsoft.com/about",
    "news.microsoft.com",
    "go.microsoft.com",
    "choice.microsoft.com",
    "microsoft-edge://",
]

SKIP_TEXT_PATTERNS = ["抽奖", "sweepstakes"]

COMPLETED_TEXT_PATTERNS = ["已完成", "completed"]

TASK_TYPE_KEYWORDS = {
    "quiz": ["quiz", "测验"],
    "poll": ["poll", "投票"],
}

POINTS_SELECTOR = ".text-caption1Stronger"

COMPLETED_CIRCLE_CLASS = "bg-statusSuccessBg3"
INCOMPLETE_CIRCLE_CLASS = "border-neutralStroke1"

LOGIN_SELECTORS = [
    'input[name="loginfmt"]',
    'input[type="email"]',
    "#i0116",
]

EARN_LINK_SELECTOR = 'a[href="/earn"], a[href^="/earn?"], a[href*="rewards.bing.com/earn"]'


class TaskParser:
    """Parser for Microsoft Rewards dashboard tasks"""

    TASK_SECTIONS = ["section#streaks", "section#offers", "section#snapshot", "section#dailyset"]

    EARN_URL = "https://rewards.bing.com/earn"

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.debug_mode = config.get("task_system.debug_mode", False) if config else False

    async def discover_tasks(self, page: Page) -> list[TaskMetadata]:
        """
        Navigate to earn page and discover all available tasks.
        Strategy: Navigate to dashboard first, then click the "赢取" link to earn page.
        This ensures proper page rendering.
        """
        self.logger.info("Discovering tasks from earn page...")

        try:
            current_url = page.url
            on_earn_page = "/earn" in current_url or "earn" in current_url.split("/")[-1]

            if not on_earn_page:
                self.logger.info(f"当前不在earn页面 ({current_url})")

                if "dashboard" not in current_url:
                    self.logger.info("导航到dashboard...")
                    await page.goto(
                        "https://rewards.bing.com/dashboard",
                        wait_until="networkidle",
                        timeout=60000,
                    )
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(2000)

                self.logger.info("Clicking earn link to navigate to earn page...")
                earn_link = page.locator(EARN_LINK_SELECTOR)
                if await earn_link.count() > 0:
                    await earn_link.first.click()
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)
                else:
                    self.logger.warning("Earn link not found, navigating directly...")
                    await page.goto(self.EARN_URL, wait_until="networkidle", timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)

            await self._wait_for_dashboard(page)

            self.logger.info(f"Final URL: {page.url}")
            try:
                page_title = await page.title()
                self.logger.info(f"Page title: {page_title}")
            except Exception:
                pass

            if await self._is_login_page(page):
                self.logger.error("Detected login page, cannot discover tasks")
                self.logger.info("  提示: 会话可能已过期，请重新登录")
                return []

            await self._wait_for_content_load(page)

            tasks = await self._parse_tasks_from_page(page)

            self.logger.info(f"Discovered {len(tasks)} tasks")

            if self.debug_mode:
                await self._save_diagnostics(page, "task_discovery")

            return tasks

        except PlaywrightTimeout:
            self.logger.error("Timeout while loading dashboard")
            return []
        except Exception as e:
            self.logger.error(f"Error discovering tasks: {e}")
            return []

    async def _wait_for_dashboard(self, page: Page):
        """Wait for OAuth redirects to complete and land on earn page"""
        max_wait_attempts = 5
        for attempt in range(max_wait_attempts):
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)

            current_url = page.url
            self.logger.info(f"Current URL (attempt {attempt + 1}): {current_url}")

            on_rewards = "rewards.microsoft.com" in current_url or "rewards.bing.com" in current_url
            if on_rewards:
                break

            if "login.live.com" in current_url or "login.microsoftonline.com" in current_url:
                self.logger.info("  检测到 OAuth 页面，等待自动登录完成...")
                try:
                    await page.wait_for_url("**/rewards.*", timeout=15000)
                    self.logger.info("  OAuth 自动登录成功，已跳转到 rewards 页面")
                except PlaywrightTimeout:
                    self.logger.warning("  OAuth 自动登录超时，尝试直接导航到 earn 页面...")
                    try:
                        await page.goto(
                            self.EARN_URL,
                            wait_until="networkidle",
                            timeout=30000,
                        )
                        await page.wait_for_timeout(2000)
                        new_url = page.url
                        self.logger.info(f"  导航后 URL: {new_url}")
                        if "rewards" in new_url:
                            self.logger.info("  成功导航到 earn 页面")
                            break
                    except Exception as e:
                        self.logger.warning(f"  导航失败: {e}")
            else:
                break

        final_url = page.url
        self.logger.info(f"Final URL: {final_url}")

        if "login" in final_url.lower() or "oauth" in final_url.lower():
            self.logger.warning("  最终仍在 OAuth 页面，检查页面内容...")
            try:
                has_earn_content = await page.evaluate("""
                    () => {
                        const sections = document.querySelectorAll('section#dailyset, section#streaks, section[id*="daily"], [class*="earn"], [class*="card"]');
                        return sections.length > 0;
                    }
                """)
                if has_earn_content:
                    self.logger.info("  页面已包含 earn 内容，继续执行")
                else:
                    self.logger.warning("  页面不包含 earn 内容，尝试强制导航...")
                    await page.goto(
                        self.EARN_URL,
                        wait_until="networkidle",
                        timeout=30000,
                    )
                    await page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.warning(f"  内容检查失败: {e}")

    async def _wait_for_content_load(self, page: Page):
        """
        Wait for React async content to finish loading.
        The new dashboard uses skeleton loaders (animate-pulse) while fetching data.
        We need to wait for these to be replaced with actual content.
        """
        self.logger.info("Waiting for dashboard content to load...")

        try:
            accept_btn = page.locator("button:has-text('Accept'), button:has-text('接受')")
            if await accept_btn.count() > 0:
                self.logger.info("  Found cookie consent banner, accepting...")
                await accept_btn.first.click()
                await page.wait_for_timeout(1000)
        except Exception as e:
            self.logger.debug(f"  No cookie consent banner: {e}")

        max_attempts = 30

        current_url = (getattr(page, "url", "") or "").lower()
        if any(token in current_url for token in ("login", "signin", "oauth", "consent")):
            self.logger.info(
                f"  Detected login/OAuth page ({current_url[:50]}...), redirecting to earn page"
            )
            try:
                await page.goto(self.EARN_URL, wait_until="networkidle", timeout=30000)
            except Exception as e:
                self.logger.debug(f"  Redirect failed: {e}")

        for i in range(max_attempts):
            try:
                result = await page.evaluate("""
                    () => {
                        const main = document.querySelector('main, [role="main"]') || document.body;
                        const links = main.querySelectorAll('a[href]');
                        let taskLinks = 0;
                        for (const link of links) {
                            const href = link.getAttribute('href') || '';
                            const text = link.innerText || '';
                            if ((href.includes('bing.com/search') ||
                                href.includes('bing.com/spotlight') ||
                                href.includes('/earn/quest') ||
                                href.includes('form=ML2')) && text.length > 5) {
                                taskLinks++;
                            }
                        }
                        const hasSection = main.querySelector('section') !== null;
                        const hasContent = main.innerText.length > 100;
                        return {
                            taskLinks: taskLinks,
                            totalLinks: links.length,
                            hasSection: hasSection,
                            hasContent: hasContent
                        };
                    }
                """)

                task_links = result.get("taskLinks", 0)
                total_links = result.get("totalLinks", 0)
                has_section = result.get("hasSection", False)
                has_content = result.get("hasContent", False)

                self.logger.debug(
                    f"  Check: {task_links} task links, {total_links} total, section={has_section}, content={has_content} (attempt {i + 1})"
                )

                if task_links >= 1:
                    self.logger.info(f"  Found {task_links} task links after {i + 1} checks")
                    await page.wait_for_timeout(2000)
                    return

                if has_section and has_content and i >= 5:
                    self.logger.info(
                        f"  Page loaded with sections but no task links after {i + 1}s"
                    )
                    await page.wait_for_timeout(2000)
                    return

            except Exception as e:
                self.logger.debug(f"  Error checking links: {e}")

            await page.wait_for_timeout(1000)

        self.logger.warning(f"  Content load check completed after {max_attempts}s")

    async def _is_login_page(self, page: Page) -> bool:
        """Check if currently on login page"""
        try:
            for selector in LOGIN_SELECTORS:
                element = await page.query_selector(selector)
                if element:
                    return True

            return False
        except Exception:
            return False

    async def _parse_tasks_from_page(self, page: Page) -> list[TaskMetadata]:
        """
        Parse task elements from the earn page.
        Page structure (4 sections):
        1. 连胜 (Streak) - stamp collection, manual claim
        2. 升级活动 (Level up) - special bonuses
        3. 任务 (Tasks) - card container with multiple <a> links
        4. 继续赚取 (Continue earning) - URL tasks with point circles

        Completion status detection:
        - Completed: circleClass contains 'bg-statusSuccessBg3'
        - Incomplete: circleClass contains 'border border-neutralStroke1'
        """
        tasks = []

        try:
            raw_tasks = await page.evaluate(
                """
                ([skipHrefs, skipTextPatterns, completedTextPatterns, pointsSelector, completedCircleClass, incompleteCircleClass]) => {
                    const tasks = [];
                    const seenHrefs = new Set();
                    const debug = [];

                    function shouldSkip(href, text) {
                        const hrefLower = href.toLowerCase();
                        const combined = (href + ' ' + text).toLowerCase();

                        if (hrefLower.startsWith('microsoft-edge://')) return true;
                        if (hrefLower.includes('xbox.com')) return true;

                        if (hrefLower === '#' || hrefLower.endsWith('#')) return true;

                        for (const skip of skipHrefs) {
                            if (skip.startsWith('/') || skip === '/') {
                                if (hrefLower === skip || hrefLower.endsWith(skip)) return true;
                                if (hrefLower.startsWith(skip + '?')) return true;
                            } else {
                                if (hrefLower.includes(skip)) return true;
                            }
                        }

                        for (const pattern of skipTextPatterns) {
                            if (combined.includes(pattern.toLowerCase())) return true;
                        }

                        if (hrefLower.includes('referandearn') || hrefLower.includes('/redeem')) return true;

                        return false;
                    }

                    function extractPoints(el) {
                        const pointsEl = el.querySelector(pointsSelector);
                        if (pointsEl) {
                            const num = pointsEl.innerText.trim().match(/\\d+/);
                            if (num) return parseInt(num[0]);
                        }

                        const text = el.innerText || '';
                        const match = text.match(/\\+(\\d+)/) ||
                                     text.match(/(\\d+)\\s*(?:points?|pts?|积分|分)/i);
                        if (match) return parseInt(match[1]);
                        return 0;
                    }

                    function isCompleted(el) {
                        const text = (el.innerText || '').toLowerCase();

                        for (const pattern of completedTextPatterns) {
                            if (text.includes(pattern.toLowerCase())) return true;
                        }

                        const progressMatch = text.match(/(\\d+)\\/(\\d+)/);
                        if (progressMatch && progressMatch[1] === progressMatch[2]) return true;

                        const circleEl = el.querySelector('[class*="rounded-full"]');
                        if (circleEl) {
                            const circleClass = circleEl.className || '';
                            if (circleClass.includes(completedCircleClass)) return true;
                            if (circleClass.includes(incompleteCircleClass)) return false;

                            const style = window.getComputedStyle(circleEl);
                            const bgColor = style.backgroundColor || '';
                            if (bgColor.includes('rgb') && !bgColor.includes('rgba(0, 0, 0, 0)')) {
                                return true;
                            }
                        }

                        const checkmark = el.querySelector('[class*="checkmark"], [aria-label*="complete"], [aria-label*="done"]');
                        if (checkmark) return true;

                        return false;
                    }

                    function extractTitle(el) {
                        const text = el.innerText || '';
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 2);

                        for (const line of lines) {
                            if (line.match(/^\\d+$/) || line.match(/^\\d+\\/\\d+/)) continue;
                            if (line.includes('到期') || line.includes('过期')) continue;
                            if (line.match(/^\\+?\\d+\\s*(积分|points?)?$/i)) continue;
                            return line.substring(0, 100);
                        }
                        return '';
                    }

                    function getTaskType(href, text) {
                        const combined = (href + ' ' + text).toLowerCase();
                        if (combined.includes('quiz') || combined.includes('测验')) return 'quiz';
                        if (combined.includes('poll') || combined.includes('投票')) return 'poll';
                        return 'urlreward';
                    }

                    const main = document.querySelector('main, [role="main"]') || document.body;
                    const links = main.querySelectorAll('a[href]');
                    debug.push('Total links: ' + links.length);

                    for (const link of links) {
                        const href = link.getAttribute('href') || '';
                        if (!href || seenHrefs.has(href)) continue;

                        const text = link.innerText || '';
                        debug.push('Checking: ' + href.substring(0, 50) + ' | text: ' + text.substring(0, 30));

                        if (shouldSkip(href, text)) {
                            debug.push('  Skipped by shouldSkip');
                            continue;
                        }

                        seenHrefs.add(href);

                        const title = extractTitle(link);
                        debug.push('  Title: ' + title);
                        if (!title) continue;

                        const points = extractPoints(link);
                        const completed = isCompleted(link);
                        const taskType = getTaskType(href, text);

                        tasks.push({
                            title: title,
                            href: href,
                            points: points,
                            taskType: taskType,
                            completed: completed
                        });
                    }

                    return { tasks: tasks, debug: debug };
                }
            """,
                [
                    SKIP_HREFS,
                    SKIP_TEXT_PATTERNS,
                    COMPLETED_TEXT_PATTERNS,
                    POINTS_SELECTOR,
                    COMPLETED_CIRCLE_CLASS,
                    INCOMPLETE_CIRCLE_CLASS,
                ],
            )

            if not raw_tasks:
                self.logger.warning("No task elements found on page")
                await self._save_diagnostics(page)
                return tasks

            debug_info = raw_tasks.get("debug", [])
            task_list = raw_tasks.get("tasks", [])

            for line in debug_info[:20]:
                self.logger.debug(f"  JS DEBUG: {line}")

            self.logger.info(f"Found {len(task_list)} potential task elements")

            for i, raw in enumerate(task_list):
                try:
                    title = raw.get("title", f"Task {i + 1}")
                    href = raw.get("href", "")
                    points = raw.get("points", 0)
                    task_type = raw.get("taskType", "urlreward")
                    completed = raw.get("completed", False)
                    section_id = raw.get("sectionId", "")

                    metadata = TaskMetadata(
                        task_id=f"{section_id}_{i}",
                        task_type=task_type,
                        title=title,
                        points=points,
                        is_completed=completed,
                        destination_url=href,
                        promotion_type=task_type,
                    )
                    tasks.append(metadata)
                    self.logger.debug(
                        f"  ✓ Parsed: {title} (type={task_type}, pts={points}, done={completed})"
                    )
                except Exception as e:
                    self.logger.debug(f"  ✗ Failed to parse task {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing tasks from page: {e}")
            await self._save_diagnostics(page)

        return tasks

    async def _save_diagnostics(self, page: Page, reason: str = "no_tasks"):
        """Save diagnostic screenshot and HTML for debugging"""
        if not self.debug_mode:
            self.logger.info("💡 提示: 在config.yaml中启用task_system.debug_mode以保存诊断数据")
            return

        import os
        from datetime import datetime

        os.makedirs("logs/diagnostics", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            screenshot_path = f"logs/diagnostics/{reason}_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            self.logger.warning(f"📸 截图已保存: {screenshot_path}")

            html = await page.content()
            html_path = f"logs/diagnostics/{reason}_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self.logger.warning(f"📄 HTML已保存: {html_path}")

            self.logger.warning("⚠️ 诊断数据已收集 - 请检查这些文件以分析问题")
        except Exception as e:
            self.logger.error(f"保存诊断数据失败: {e}")

    def _determine_task_type(self, promotion_type: str) -> str:
        """Determine task type from promotion type"""
        promotion_type_lower = promotion_type.lower()

        if "quiz" in promotion_type_lower:
            return "quiz"
        elif "poll" in promotion_type_lower:
            return "poll"
        elif "urlreward" in promotion_type_lower or "url" in promotion_type_lower:
            return "urlreward"
        else:
            return "urlreward"
