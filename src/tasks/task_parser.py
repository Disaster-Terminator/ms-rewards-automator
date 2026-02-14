"""
Task Parser for extracting task information from Microsoft Rewards dashboard
Supports the new React-based rewards.bing.com dashboard (2025+)
"""

import logging
import re
from typing import List, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from tasks.task_base import TaskMetadata


class TaskParser:
    """Parser for Microsoft Rewards dashboard tasks"""
    
    # Sections on the dashboard that contain tasks
    TASK_SECTIONS = ["section#dailyset", "section#streaks", "section#offers"]
    
    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.debug_mode = config.get("task_system.debug_mode", False) if config else False
    
    async def discover_tasks(self, page: Page) -> List[TaskMetadata]:
        """
        Navigate to dashboard and discover all available tasks
        """
        self.logger.info("Discovering tasks from dashboard...")
        
        try:
            # Navigate to rewards dashboard if not already there
            current_url = page.url
            on_rewards_page = "rewards.microsoft.com" in current_url or "rewards.bing.com" in current_url
            if not on_rewards_page:
                await page.goto(
                    "https://rewards.bing.com/",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
            
            # Wait for OAuth redirect to complete (if any)
            await self._wait_for_dashboard(page)
            
            # DIAGNOSTIC: Log current state
            self.logger.info(f"Final URL: {page.url}")
            try:
                page_title = await page.title()
                self.logger.info(f"Page title: {page_title}")
            except Exception:
                pass
            
            # Check if on login page
            if await self._is_login_page(page):
                self.logger.error("Detected login page, cannot discover tasks")
                self.logger.info("  提示: 会话可能已过期，请重新登录")
                return []
            
            # Wait for React content to finish loading
            await self._wait_for_content_load(page)
            
            # Parse tasks from the page
            tasks = await self._parse_tasks_from_page(page)
            
            self.logger.info(f"Discovered {len(tasks)} tasks")
            return tasks
            
        except PlaywrightTimeout:
            self.logger.error("Timeout while loading dashboard")
            return []
        except Exception as e:
            self.logger.error(f"Error discovering tasks: {e}")
            return []

    async def _wait_for_dashboard(self, page: Page):
        """Wait for OAuth redirects to complete and land on rewards page"""
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
                    self.logger.warning("  OAuth 自动登录超时，尝试直接导航到 dashboard...")
                    try:
                        await page.goto("https://rewards.bing.com/dashboard", wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)
                        new_url = page.url
                        self.logger.info(f"  导航后 URL: {new_url}")
                        if "rewards" in new_url:
                            self.logger.info("  成功导航到 dashboard")
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
                has_dashboard_content = await page.evaluate("""
                    () => {
                        const sections = document.querySelectorAll('section#dailyset, section#streaks, section[id*="daily"]');
                        return sections.length > 0;
                    }
                """)
                if has_dashboard_content:
                    self.logger.info("  页面已包含 dashboard 内容，继续执行")
                else:
                    self.logger.warning("  页面不包含 dashboard 内容，尝试强制导航...")
                    await page.goto("https://rewards.bing.com/dashboard", wait_until="networkidle", timeout=30000)
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
        
        section_selectors = ["section#dailyset", "section#streaks", "section[id*='daily']", "section[id*='streak']"]
        section_found = False
        
        for selector in section_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                self.logger.debug(f"  Found section: {selector}")
                section_found = True
                break
            except PlaywrightTimeout:
                continue
        
        if not section_found:
            self.logger.warning("  No task sections found, waiting for page to stabilize...")
            await page.wait_for_timeout(3000)
        
        max_attempts = 10
        for i in range(max_attempts):
            try:
                current_url = page.url
                if "login" in current_url.lower() or "oauth" in current_url.lower():
                    self.logger.warning("  Page navigated away, attempting to return to dashboard...")
                    await page.goto("https://rewards.bing.com/dashboard", wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2000)
            except Exception:
                pass
            
            try:
                skeleton_count = await page.evaluate("""
                    () => {
                        const skeletons = document.querySelectorAll('.animate-pulse, [class*="skeleton"], [class*="loading"]');
                        return skeletons.length;
                    }
                """)
                
                if skeleton_count == 0:
                    self.logger.info(f"  Dashboard content loaded (after {i + 1} checks)")
                    return
                
                self.logger.debug(f"  Still loading... ({skeleton_count} skeletons remaining)")
            except Exception as e:
                self.logger.debug(f"  Error checking skeletons: {e}")
            
            await page.wait_for_timeout(1000)
        
        self.logger.warning(f"  Content may not be fully loaded after {max_attempts}s")
    
    async def _is_login_page(self, page: Page) -> bool:
        """Check if currently on login page"""
        try:
            login_selectors = [
                'input[name="loginfmt"]',
                'input[type="email"]',
                '#i0116',
            ]
            
            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    return True
            
            return False
        except Exception:
            return False
    
    async def _parse_tasks_from_page(self, page: Page) -> List[TaskMetadata]:
        """
        Parse task elements from the dashboard page.
        Uses JavaScript evaluation to extract structured task data from the React DOM.
        """
        tasks = []
        
        try:
            raw_tasks = await page.evaluate("""
                () => {
                    const tasks = [];
                    
                    const sectionIds = ['dailyset', 'streaks', 'offers', 'snapshot'];
                    let sections = [];
                    
                    for (const sectionId of sectionIds) {
                        const section = document.querySelector(`section#${sectionId}`);
                        if (section) sections.push({id: sectionId, el: section});
                    }
                    
                    if (sections.length === 0) {
                        sections = Array.from(document.querySelectorAll('section')).map(s => ({
                            id: s.id || 'unknown',
                            el: s
                        }));
                    }
                    
                    if (sections.length === 0) {
                        const mainContent = document.querySelector('main, [role="main"], #main, .main-content');
                        if (mainContent) {
                            sections = [{id: 'main', el: mainContent}];
                        }
                    }
                    
                    for (const {id: sectionId, el: section} of sections) {
                        const cards = section.querySelectorAll('a[href], button[href], [role="link"]');
                        
                        for (const card of cards) {
                            const href = card.getAttribute('href') || card.getAttribute('data-href') || '';
                            
                            if (href === '/earn' || href === '/dashboard' || 
                                href === '/redeem' || href === '/about' || href === '/refer' ||
                                href === '/' || href === '#') {
                                continue;
                            }
                            
                            const text = card.innerText || '';
                            const ariaLabel = card.getAttribute('aria-label') || '';
                            
                            let title = '';
                            const headings = card.querySelectorAll('h3, h4, p, span, div');
                            for (const h of headings) {
                                const t = h.innerText.trim();
                                if (t && t.length > 2 && t.length < 200) {
                                    title = t;
                                    break;
                                }
                            }
                            if (!title) {
                                title = ariaLabel || text.substring(0, 80).trim();
                            }
                            
                            if (!title && !href) continue;
                            
                            let points = 0;
                            const pointsMatch = text.match(/(\\d+)\\s*(?:points?|pts?|积分)/i);
                            if (pointsMatch) {
                                points = parseInt(pointsMatch[1]);
                            } else {
                                const numMatch = text.match(/\\+(\\d+)/);
                                if (numMatch) points = parseInt(numMatch[1]);
                            }
                            
                            let taskType = 'urlreward';
                            const combined = (href + ' ' + text + ' ' + ariaLabel).toLowerCase();
                            if (combined.includes('quiz') || combined.includes('测验')) {
                                taskType = 'quiz';
                            } else if (combined.includes('poll') || combined.includes('投票')) {
                                taskType = 'poll';
                            }
                            
                            let completed = false;
                            const completedEl = card.querySelector(
                                '[class*="completed"], [class*="done"], [class*="check"], ' +
                                'svg[class*="check"], [aria-label*="Completed"], [aria-label*="完成"]'
                            );
                            if (completedEl) completed = true;
                            if (ariaLabel.toLowerCase().includes('completed') || 
                                ariaLabel.includes('完成')) {
                                completed = true;
                            }
                            
                            tasks.push({
                                sectionId: sectionId,
                                title: title,
                                href: href,
                                points: points,
                                taskType: taskType,
                                completed: completed,
                                ariaLabel: ariaLabel
                            });
                        }
                    }
                    
                    return tasks;
                }
            """)
            
            if not raw_tasks:
                self.logger.warning("No task elements found on page")
                await self._save_diagnostics(page)
                return tasks
            
            self.logger.info(f"Found {len(raw_tasks)} potential task elements")
            
            for i, raw in enumerate(raw_tasks):
                try:
                    title = raw.get('title', f'Task {i + 1}')
                    href = raw.get('href', '')
                    points = raw.get('points', 0)
                    task_type = raw.get('taskType', 'urlreward')
                    completed = raw.get('completed', False)
                    section_id = raw.get('sectionId', '')
                    
                    metadata = TaskMetadata(
                        task_id=f"{section_id}_{i}",
                        task_type=task_type,
                        title=title,
                        points=points,
                        is_completed=completed,
                        destination_url=href,
                        promotion_type=task_type
                    )
                    tasks.append(metadata)
                    self.logger.debug(f"  ✓ Parsed: {title} (type={task_type}, pts={points}, done={completed})")
                except Exception as e:
                    self.logger.debug(f"  ✗ Failed to parse task {i}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing tasks from page: {e}")
            await self._save_diagnostics(page)
        
        return tasks
    
    async def _save_diagnostics(self, page: Page):
        """Save diagnostic screenshot and HTML for debugging"""
        if not self.debug_mode:
            self.logger.info("💡 提示: 在config.yaml中启用task_system.debug_mode以保存诊断数据")
            return
        
        import os
        from datetime import datetime
        os.makedirs("logs/diagnostics", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            screenshot_path = f"logs/diagnostics/no_tasks_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            self.logger.warning(f"📸 截图已保存: {screenshot_path}")
            
            html = await page.content()
            html_path = f"logs/diagnostics/no_tasks_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self.logger.warning(f"📄 HTML已保存: {html_path}")
            
            self.logger.warning("⚠️ 诊断数据已收集 - 请检查这些文件以分析问题")
        except Exception as e:
            self.logger.error(f"保存诊断数据失败: {e}")
    
    def _determine_task_type(self, promotion_type: str) -> str:
        """Determine task type from promotion type"""
        promotion_type_lower = promotion_type.lower()
        
        if 'quiz' in promotion_type_lower:
            return 'quiz'
        elif 'poll' in promotion_type_lower:
            return 'poll'
        elif 'urlreward' in promotion_type_lower or 'url' in promotion_type_lower:
            return 'urlreward'
        else:
            return 'urlreward'
