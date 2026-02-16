"""
Quiz Task Handler

Handles interactive quiz tasks. This is a basic implementation that attempts
to answer quiz questions.
"""

import asyncio
import logging
import random
from datetime import datetime
from pathlib import Path

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from tasks.task_base import Task, TaskMetadata


class QuizTask(Task):
    """Handler for quiz tasks"""

    def __init__(self, metadata: TaskMetadata):
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)

    async def execute(self, page: Page) -> bool:
        """
        Execute quiz task

        Args:
            page: Playwright page object

        Returns:
            True if task completed successfully, False otherwise
        """
        self.logger.info(f"❓ 执行Quiz任务: {self.metadata.title}")

        if not self.metadata.destination_url:
            self.logger.error("❌ 未提供目标URL")
            return False

        try:
            # Navigate to the quiz with longer timeout
            self.logger.debug(f"🌐 导航到Quiz: {self.metadata.destination_url}")
            try:
                await page.goto(
                    self.metadata.destination_url,
                    wait_until="domcontentloaded",  # 改为更宽松的等待条件
                    timeout=60000,  # 增加到60秒
                )
            except PlaywrightTimeout:
                self.logger.warning("Page load timeout, but continuing...")
                # 保存截图用于调试
                await self._save_debug_screenshot(page, "quiz_timeout")

            # Wait for quiz to load
            await asyncio.sleep(3)  # 增加等待时间

            # Attempt to answer quiz questions
            self.logger.info("🎯 查找Quiz问题...")
            questions_answered = await self._answer_quiz_questions(page)

            if questions_answered > 0:
                self.logger.info(f"✅ 已回答 {questions_answered} 个问题")
                return True
            else:
                self.logger.warning("⚠️  未找到或未回答任何问题")
                return False

        except PlaywrightTimeout:
            self.logger.error("❌ 加载Quiz超时")
            await self._save_debug_screenshot(page, "quiz_timeout")
            return False
        except Exception as e:
            self.logger.error(f"❌ 执行Quiz任务出错: {e}")
            await self._save_debug_screenshot(page, "quiz_error")
            return False

    async def _answer_quiz_questions(self, page: Page) -> int:
        """
        Answer quiz questions

        Args:
            page: Playwright page object

        Returns:
            Number of questions answered
        """
        questions_answered = 0
        max_questions = 10  # Safety limit

        try:
            for i in range(max_questions):
                self.logger.debug(f"Looking for question {i + 1}...")

                # Wait a bit for question to appear
                await asyncio.sleep(1)

                # Look for answer options
                answer_found = await self._select_answer(page)

                if not answer_found:
                    self.logger.debug("No more questions found")
                    break

                questions_answered += 1

                # Wait for next question or completion
                await asyncio.sleep(2)

                # Check if quiz is complete
                if await self._is_quiz_complete(page):
                    self.logger.debug("Quiz completed")
                    break

        except Exception as e:
            self.logger.error(f"Error answering questions: {e}")

        return questions_answered

    async def _select_answer(self, page: Page) -> bool:
        """
        Select an answer for the current question

        Args:
            page: Playwright page object

        Returns:
            True if answer was selected, False otherwise
        """
        try:
            # Strategy 1: Try common quiz option selectors
            answer_selectors = [
                ".rqOption",  # Rewards quiz
                "div.rqOption",  # 标准quiz选项
                "a.rqOption",  # 链接形式的选项
                '[class*="quiz-option"]',
                '[class*="answer-option"]',
                'button[class*="option"]',
                ".wk-button",
                # ABC Quiz specific selectors
                'input[type="radio"]',  # 单选按钮
                'input[type="checkbox"]',  # 多选按钮
                'button[id*="rqAnswerOption"]',  # Rewards答案按钮
                '[id*="rqAnswerOption"]',  # 任何答案选项ID
                # 避免选择MORE和Feedback按钮
                'div[class*="option"]:not([class*="more"]):not([class*="feedback"])',
            ]

            self.logger.debug("🔍 尝试查找答案选项...")

            for selector in answer_selectors:
                options = await page.query_selector_all(selector)
                if options and len(options) > 0:
                    self.logger.debug(f"  找到 {len(options)} 个选项 (选择器: {selector})")

                    # Filter out non-visible or disabled options
                    visible_options = []
                    for opt in options:
                        try:
                            if await opt.is_visible() and await opt.is_enabled():
                                visible_options.append(opt)
                        except Exception:
                            continue

                    if visible_options:
                        self.logger.debug(f"  其中 {len(visible_options)} 个可见且可用")
                        # Select a random visible option
                        selected_option = random.choice(visible_options)
                        await selected_option.click()
                        self.logger.info(f"  ✓ 已选择答案 (选择器: {selector})")
                        return True
                    else:
                        self.logger.debug("  但没有可见且可用的选项")

            # Strategy 2: Look for elements containing option text (A., B., C., etc.)
            self.logger.debug("🔍 尝试通过文本模式查找...")
            option_patterns = ["A.", "B.", "C.", "D.", "E."]
            for pattern in option_patterns:
                try:
                    # Try to find clickable elements containing the pattern
                    element = await page.query_selector(f'text="{pattern}"')
                    if element:
                        # Get the parent clickable element
                        parent = await element.evaluate_handle(
                            'el => el.closest("button, a, div[role=button], [onclick]")'
                        )
                        if parent:
                            await parent.as_element().click()
                            self.logger.info(f"  ✓ 已选择答案 (文本模式: {pattern})")
                            return True
                except Exception:
                    continue

            # Strategy 3: Save diagnostic screenshot
            self.logger.warning("⚠️ 未找到任何答案选项，保存诊断截图...")
            await self._save_debug_screenshot(page, "no_options_found")

            return False

        except Exception as e:
            self.logger.error(f"选择答案时出错: {e}")
            await self._save_debug_screenshot(page, "select_error")
            return False

    async def _is_quiz_complete(self, page: Page) -> bool:
        """
        Check if quiz is complete

        Args:
            page: Playwright page object

        Returns:
            True if quiz is complete, False otherwise
        """
        try:
            completion_indicators = [
                'text="Congratulations"',
                'text="Quiz Complete"',
                'text="You earned"',
                '[class*="quiz-complete"]',
                '[class*="success"]',
            ]

            for indicator in completion_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=1000, state="visible")
                    if element:
                        return True
                except PlaywrightTimeout:
                    continue

            return False

        except Exception as e:
            self.logger.debug(f"Error checking quiz completion: {e}")
            return False

    async def _save_debug_screenshot(self, page: Page, reason: str) -> None:
        """
        Save debug screenshot

        Args:
            page: Playwright page object
            reason: Reason for screenshot (e.g., "timeout", "error")
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("logs/diagnostics")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshot_dir / f"task_quiz_{reason}_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path))
            self.logger.info(f"🔍 Debug screenshot saved: {screenshot_path}")

        except Exception as e:
            self.logger.debug(f"Failed to save debug screenshot: {e}")
