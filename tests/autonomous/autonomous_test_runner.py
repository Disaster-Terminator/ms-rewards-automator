"""
自主测试运行器
支持无头模式运行、自动问题发现、诊断和报告生成
"""

import asyncio
import logging
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .diagnostic_engine import DiagnosisResult, DiagnosticEngine
from .page_inspector import DetectedIssue, IssueSeverity, PageInspector
from .reporter import TestReporter, TestStep
from .screenshot_manager import ScreenshotManager

logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """测试配置"""

    headless: bool = True
    auto_screenshot: bool = True
    screenshot_on_error: bool = True
    stop_on_critical: bool = True
    max_retries: int = 3
    page_timeout: int = 30000
    inspection_interval: int = 5


class AutonomousTestRunner:
    """自主测试运行器"""

    def __init__(self, config_path: str = "config.yaml", test_config: TestConfig | None = None):
        self.config_path = config_path
        self.test_config = test_config or TestConfig()

        self.screenshot_manager = ScreenshotManager()
        self.page_inspector = PageInspector()
        self.diagnostic_engine = DiagnosticEngine()
        self.reporter = TestReporter()

        self.config = None
        self.browser = None
        self.context = None
        self.page = None

        self.current_test_name = ""
        self.test_steps: list[TestStep] = []
        self.test_issues: list[DetectedIssue] = []
        self.test_diagnoses: list[DiagnosisResult] = []

        self.operation_count = 0

        logger.info("自主测试运行器初始化完成")

    async def initialize(self) -> bool:
        """初始化测试环境"""
        try:
            from infrastructure.config_manager import ConfigManager

            self.config = ConfigManager(self.config_path)

            if self.test_config.headless:
                self.config.config["browser"]["headless"] = True

            logger.info("测试环境初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def create_browser(self) -> bool:
        """创建浏览器实例"""
        try:
            from playwright.async_api import async_playwright

            logger.info("创建浏览器实例...")

            playwright = await async_playwright().start()

            browser_type = self.config.get("browser.type", "chromium")
            if browser_type == "chromium":
                self.browser = await playwright.chromium.launch(
                    headless=self.test_config.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )
            elif browser_type == "firefox":
                self.browser = await playwright.firefox.launch(headless=self.test_config.headless)
            else:
                self.browser = await playwright.webkit.launch(headless=self.test_config.headless)

            logger.info("✓ 浏览器创建成功")
            return True

        except Exception as e:
            logger.error(f"创建浏览器失败: {e}")
            return False

    async def create_context(self, storage_state: str | None = None) -> bool:
        """创建浏览器上下文"""
        try:
            context_options = {
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            if storage_state and Path(storage_state).exists():
                context_options["storage_state"] = storage_state
                logger.info(f"加载会话状态: {storage_state}")

            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()

            self.page.set_default_timeout(self.test_config.page_timeout)

            logger.info("✓ 浏览器上下文创建成功")
            return True

        except Exception as e:
            logger.error(f"创建上下文失败: {e}")
            return False

    async def run_test(self, test_name: str, test_func: Callable, *args, **kwargs) -> bool:
        """
        运行单个测试

        Args:
            test_name: 测试名称
            test_func: 测试函数
            *args, **kwargs: 测试函数参数

        Returns:
            测试是否通过
        """
        self.current_test_name = test_name
        self.test_steps = []
        self.test_issues = []
        self.test_diagnoses = []

        start_time = self.reporter.start_test(test_name)
        status = "passed"

        logger.info(f"\n{'=' * 60}")
        logger.info(f"开始测试: {test_name}")
        logger.info(f"{'=' * 60}")

        try:
            await test_func(self, *args, **kwargs)

            if self.test_issues:
                critical_issues = [
                    i
                    for i in self.test_issues
                    if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]
                ]
                if critical_issues:
                    status = "failed"
                else:
                    status = "passed"

        except Exception as e:
            logger.error(f"测试异常: {e}")
            status = "error"

            if self.test_config.screenshot_on_error and self.page:
                await self.screenshot_manager.capture_on_error(self.page, e, test_name)

            self.test_issues.append(
                DetectedIssue(
                    issue_type=self.page_inspector._map_exception_to_issue_type(e),
                    severity=IssueSeverity.ERROR,
                    title="测试执行异常",
                    description=str(e),
                    suggestions=["检查异常堆栈", "验证测试环境"],
                )
            )

        self.test_diagnoses = self.diagnostic_engine.diagnose(self.test_issues)

        self.reporter.end_test(
            test_name, status, start_time, self.test_steps, self.test_issues, self.test_diagnoses
        )

        log_status = "✅ 通过" if status == "passed" else f"❌ {status.upper()}"
        logger.info(f"\n测试结果: {log_status}")
        logger.info(f"发现问题: {len(self.test_issues)} 个")
        logger.info(f"诊断结果: {len(self.test_diagnoses)} 个")

        return status == "passed"

    async def execute_step(self, step_name: str, step_func: Callable, *args, **kwargs) -> bool:
        """
        执行测试步骤

        Args:
            step_name: 步骤名称
            step_func: 步骤函数
            *args, **kwargs: 步骤函数参数

        Returns:
            步骤是否成功
        """
        step_start = time.time()
        step_status = "passed"
        step_message = None
        screenshot_path = None

        logger.info(f"  执行步骤: {step_name}")

        try:
            result = await step_func(*args, **kwargs)

            if result is False:
                step_status = "failed"
                step_message = "步骤返回失败"

            self.operation_count += 1

            if (
                self.test_config.inspection_interval > 0
                and self.operation_count % self.test_config.inspection_interval == 0
            ):
                await self.inspect_current_page()

        except Exception as e:
            step_status = "failed"
            step_message = str(e)
            logger.warning(f"  步骤失败: {e}")

            if self.test_config.screenshot_on_error and self.page:
                screenshot_path = await self.screenshot_manager.capture_on_error(
                    self.page, e, step_name
                )

        if self.test_config.auto_screenshot and self.page and step_status == "passed":
            screenshot_path = await self.screenshot_manager.capture(
                self.page, step_name, context=self.current_test_name
            )

        step_duration = int((time.time() - step_start) * 1000)

        self.test_steps.append(
            TestStep(
                name=step_name,
                status=step_status,
                duration_ms=step_duration,
                message=step_message,
                screenshot=screenshot_path,
            )
        )

        return step_status == "passed"

    async def inspect_current_page(self) -> list[DetectedIssue]:
        """检查当前页面"""
        if not self.page:
            return []

        issues = await self.page_inspector.inspect_page(self.page)

        if issues:
            self.test_issues.extend(issues)

            for issue in issues:
                log_level = logging.WARNING
                if issue.severity == IssueSeverity.CRITICAL:
                    log_level = logging.ERROR
                elif issue.severity == IssueSeverity.ERROR:
                    log_level = logging.ERROR

                logger.log(log_level, f"  发现问题: [{issue.severity.value}] {issue.title}")

                if self.test_config.auto_screenshot:
                    await self.screenshot_manager.capture(
                        self.page, f"issue_{issue.issue_type.value}", context=issue.title
                    )

            if self.test_config.stop_on_critical:
                critical = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
                if critical:
                    logger.error("发现严重问题，停止测试")
                    raise Exception(f"严重问题: {critical[0].title}")

        return issues

    async def navigate_to(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """导航到URL"""

        async def _navigate():
            await self.page.goto(url, wait_until=wait_until, timeout=self.test_config.page_timeout)
            return True

        return await self.execute_step(f"导航到 {url}", _navigate)

    async def click_element(self, selector: str, description: str = "") -> bool:
        """点击元素"""
        desc = description or selector

        async def _click():
            await self.page.click(selector, timeout=10000)
            return True

        return await self.execute_step(f"点击: {desc}", _click)

    async def fill_input(self, selector: str, value: str, description: str = "") -> bool:
        """填写输入框"""
        desc = description or selector

        async def _fill():
            await self.page.fill(selector, value, timeout=10000)
            return True

        return await self.execute_step(f"填写: {desc}", _fill)

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        """等待元素出现"""

        async def _wait():
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True

        return await self.execute_step(f"等待元素: {selector}", _wait)

    async def verify_element_exists(self, selector: str, description: str = "") -> bool:
        """验证元素存在"""
        desc = description or selector
        found, issue = await self.page_inspector.verify_element(self.page, selector)

        if not found and issue:
            self.test_issues.append(issue)

        step_status = "passed" if found else "failed"
        self.test_steps.append(
            TestStep(
                name=f"验证元素: {desc}",
                status=step_status,
                duration_ms=0,
                message=None if found else f"元素未找到: {selector}",
            )
        )

        return found

    async def take_screenshot(self, name: str) -> str | None:
        """手动截图"""
        if self.page:
            return await self.screenshot_manager.capture(self.page, name)
        return None

    async def wait(self, seconds: float):
        """等待"""
        await asyncio.sleep(seconds)

    def get_diagnoses(self) -> list[DiagnosisResult]:
        """获取诊断结果"""
        return self.test_diagnoses

    def get_issues(self) -> list[DetectedIssue]:
        """获取问题列表"""
        return self.test_issues

    async def cleanup(self):
        """清理资源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()

            logger.info("资源清理完成")

        except Exception as e:
            logger.warning(f"清理资源时出错: {e}")

    def generate_reports(self) -> dict[str, str]:
        """生成报告"""
        json_report = self.reporter.generate_report()
        html_report = self.reporter.generate_html_report()

        self.screenshot_manager.save_manifest()
        self.diagnostic_engine.save_diagnosis_report()

        self.reporter.print_summary()

        return {"json": json_report, "html": html_report}

    async def run_full_test_suite(self) -> dict[str, Any]:
        """
        运行完整测试套件

        Returns:
            测试结果摘要
        """
        results = {"session_id": self.screenshot_manager.session_id, "tests": {}, "reports": {}}

        try:
            if not await self.initialize():
                raise Exception("初始化失败")

            if not await self.create_browser():
                raise Exception("创建浏览器失败")

            storage_state = self.config.get("account.storage_state_path")
            if not await self.create_context(storage_state):
                raise Exception("创建上下文失败")

            results["tests"]["login"] = await self.run_test("登录状态检测", self._test_login_status)

            results["tests"]["bing_access"] = await self.run_test(
                "Bing访问测试", self._test_bing_access
            )

            results["tests"]["search_function"] = await self.run_test(
                "搜索功能测试", self._test_search_function
            )

            results["tests"]["points_detection"] = await self.run_test(
                "积分检测测试", self._test_points_detection
            )

        except Exception as e:
            logger.error(f"测试套件执行失败: {e}")
            results["error"] = str(e)

        finally:
            await self.cleanup()

        results["reports"] = self.generate_reports()

        return results

    async def _test_login_status(self, runner):
        """测试登录状态"""
        login_url = runner.config.get("account.login_url", "https://rewards.microsoft.com/")

        await runner.execute_step(
            "导航到登录页面", lambda: runner.page.goto(login_url, wait_until="domcontentloaded")
        )

        await runner.wait(3)

        issues = await runner.inspect_current_page()

        login_issues = [i for i in issues if i.issue_type.value == "login_required"]
        if login_issues:
            logger.warning("检测到需要登录")

        await runner.take_screenshot("login_status_check")

    async def _test_bing_access(self, runner):
        """测试Bing访问"""
        await runner.execute_step(
            "导航到Bing",
            lambda: runner.page.goto("https://www.bing.com", wait_until="domcontentloaded"),
        )

        await runner.wait(2)

        await runner.verify_element_exists("#sb_form_q", "搜索框")

        await runner.take_screenshot("bing_homepage")

    async def _test_search_function(self, runner):
        """测试搜索功能"""
        await runner.navigate_to("https://www.bing.com")

        await runner.wait(1)

        search_selectors = ["#sb_form_q", "input[name='q']", "textarea[id='sb_form_q']"]

        search_found = False
        for selector in search_selectors:
            if await runner.verify_element_exists(selector, "搜索输入框"):
                search_found = True
                await runner.fill_input(selector, "test query")
                break

        if not search_found:
            logger.warning("未找到搜索框")

        await runner.take_screenshot("search_test")

    async def _test_points_detection(self, runner):
        """测试积分检测"""
        await runner.navigate_to("https://rewards.microsoft.com/")

        await runner.wait(3)

        await runner.inspect_current_page()

        await runner.take_screenshot("points_detection")
