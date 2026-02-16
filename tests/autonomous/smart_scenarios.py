"""
智能测试场景
针对 MS Rewards Automator 的专项测试场景
"""

import logging
from pathlib import Path
from typing import Any

from .autonomous_test_runner import AutonomousTestRunner
from .page_inspector import IssueType

logger = logging.getLogger(__name__)


class SmartTestScenarios:
    """智能测试场景"""

    def __init__(self, runner: AutonomousTestRunner):
        self.runner = runner
        self.results = {}

    async def run_all_scenarios(self) -> dict[str, Any]:
        """运行所有测试场景"""
        scenarios = [
            ("环境检测", self.scenario_environment_check),
            ("登录状态验证", self.scenario_login_verification),
            ("搜索功能验证", self.scenario_search_verification),
            ("积分系统验证", self.scenario_points_verification),
            ("反检测能力验证", self.scenario_anti_detection),
        ]

        for name, scenario_func in scenarios:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"执行场景: {name}")
            logger.info(f"{'=' * 60}")

            try:
                result = await self.runner.run_test(name, scenario_func)
                self.results[name] = result
            except Exception as e:
                logger.error(f"场景执行失败: {e}")
                self.results[name] = False

        return self.results

    async def scenario_environment_check(self, runner):
        """环境检测场景"""
        await runner.execute_step("检查配置文件", self._check_config_file)

        await runner.execute_step("检查会话文件", self._check_session_file)

        await runner.execute_step("检查网络连接", self._check_network)

    async def _check_config_file(self):
        """检查配置文件"""
        config_path = Path(self.runner.config_path)
        if not config_path.exists():
            raise Exception(f"配置文件不存在: {config_path}")

        required_keys = ["search.desktop_count", "search.mobile_count", "browser.type"]

        missing = []
        for key in required_keys:
            value = self.runner.config.get(key)
            if value is None:
                missing.append(key)

        if missing:
            raise Exception(f"缺少必要配置: {', '.join(missing)}")

        logger.info("  ✓ 配置文件验证通过")
        return True

    async def _check_session_file(self):
        """检查会话文件"""
        storage_path = self.runner.config.get("account.storage_state_path")

        if storage_path:
            session_file = Path(storage_path)
            if session_file.exists():
                logger.info(f"  ✓ 会话文件存在: {storage_path}")
                return True
            else:
                logger.warning(f"  ⚠ 会话文件不存在: {storage_path}")
                return True
        else:
            logger.info("  ℹ 未配置会话文件路径")
            return True

    async def _check_network(self):
        """检查网络连接"""
        import aiohttp

        test_urls = ["https://www.bing.com", "https://rewards.microsoft.com"]

        for url in test_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            logger.info(f"  ✓ {url} 可访问")
                        else:
                            logger.warning(f"  ⚠ {url} 返回状态码: {resp.status}")
            except Exception as e:
                logger.warning(f"  ⚠ {url} 连接失败: {e}")

        return True

    async def scenario_login_verification(self, runner):
        """登录状态验证场景"""
        login_url = runner.config.get("account.login_url", "https://rewards.microsoft.com/")

        await runner.navigate_to(login_url)
        await runner.wait(3)

        issues = await runner.inspect_current_page()

        login_issues = [i for i in issues if i.issue_type == IssueType.LOGIN_REQUIRED]
        captcha_issues = [i for i in issues if i.issue_type == IssueType.CAPTCHA_DETECTED]

        if captcha_issues:
            logger.error("  ✗ 检测到验证码，需要人工处理")
            raise Exception("检测到验证码")

        if login_issues:
            logger.warning("  ⚠ 需要登录")

            has_session = Path(runner.config.get("account.storage_state_path", "")).exists()

            if has_session:
                logger.warning("  ⚠ 会话文件存在但登录状态失效")
            else:
                logger.info("  ℹ 未找到会话文件")
        else:
            logger.info("  ✓ 登录状态正常")

        await runner.take_screenshot("login_verification")

    async def scenario_search_verification(self, runner):
        """搜索功能验证场景"""
        await runner.navigate_to("https://www.bing.com")
        await runner.wait(2)

        search_selectors = [
            "#sb_form_q",
            "input[name='q']",
            "textarea[id='sb_form_q']",
            "input[type='search']",
        ]

        search_found = False
        for selector in search_selectors:
            element = await runner.page.query_selector(selector)
            if element:
                search_found = True
                logger.info(f"  ✓ 找到搜索框: {selector}")

                await runner.page.fill(selector, "test search query")
                await runner.wait(0.5)

                try:
                    await runner.page.press(selector, "Enter")
                    await runner.wait(2)

                    issues = await runner.inspect_current_page()

                    if not any(i.issue_type == IssueType.CAPTCHA_DETECTED for i in issues):
                        logger.info("  ✓ 搜索功能正常")
                        await runner.take_screenshot("search_result")
                    else:
                        logger.warning("  ⚠ 搜索触发验证码")
                except Exception as e:
                    logger.warning(f"  ⚠ 搜索执行失败: {e}")

                break

        if not search_found:
            logger.error("  ✗ 未找到搜索框")
            await runner.take_screenshot("no_search_box")
            raise Exception("未找到搜索框")

    async def scenario_points_verification(self, runner):
        """积分系统验证场景"""
        await runner.navigate_to("https://rewards.microsoft.com/")
        await runner.wait(3)

        issues = await runner.inspect_current_page()

        points_selectors = [
            "span[data-bi-id='userPoints']",
            ".user-points",
            "[class*='points']",
            "span[id*='points']",
        ]

        points_found = False
        for selector in points_selectors:
            element = await runner.page.query_selector(selector)
            if element:
                try:
                    text = await element.text_content()
                    logger.info(f"  ✓ 找到积分显示: {text}")
                    points_found = True
                    break
                except Exception:
                    pass

        if not points_found:
            logger.warning("  ⚠ 未找到积分显示元素")

        await runner.take_screenshot("points_page")

        login_required = any(i.issue_type == IssueType.LOGIN_REQUIRED for i in issues)
        if login_required:
            logger.warning("  ⚠ 需要登录才能查看积分")

    async def scenario_anti_detection(self, runner):
        """反检测能力验证场景"""
        await runner.navigate_to("https://www.bing.com")
        await runner.wait(2)

        webdriver_check = await runner.page.evaluate("() => navigator.webdriver")

        if webdriver_check:
            logger.warning("  ⚠ 检测到 webdriver 标志")
        else:
            logger.info("  ✓ 未检测到 webdriver 标志")

        user_agent = await runner.page.evaluate("() => navigator.userAgent")
        logger.info(f"  ℹ User-Agent: {user_agent[:50]}...")

        plugins = await runner.page.evaluate("() => navigator.plugins.length")
        logger.info(f"  ℹ 插件数量: {plugins}")

        languages = await runner.page.evaluate("() => navigator.languages")
        logger.info(f"  ℹ 语言设置: {languages}")

        await runner.take_screenshot("anti_detection_check")

        issues = await runner.inspect_current_page()
        captcha_detected = any(i.issue_type == IssueType.CAPTCHA_DETECTED for i in issues)

        if captcha_detected:
            logger.warning("  ⚠ 检测到验证码，反检测能力可能不足")
        else:
            logger.info("  ✓ 未触发验证码")


class QuickHealthCheck:
    """快速健康检查"""

    def __init__(self, runner: AutonomousTestRunner):
        self.runner = runner

    async def run(self) -> dict[str, Any]:
        """运行快速检查"""
        results = {
            "config_valid": False,
            "network_ok": False,
            "browser_ok": False,
            "login_ok": False,
            "issues": [],
        }

        try:
            config_path = Path(self.runner.config_path)
            results["config_valid"] = config_path.exists()

            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.bing.com", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    results["network_ok"] = resp.status == 200
        except Exception:
            results["network_ok"] = False

        try:
            if self.runner.browser:
                results["browser_ok"] = self.runner.browser.is_connected()
        except Exception:
            results["browser_ok"] = False

        try:
            if self.runner.page:
                await self.runner.page.evaluate("() => 1+1")
                results["browser_ok"] = True
        except Exception:
            results["browser_ok"] = False

        return results

    def print_results(self, results: dict[str, Any]):
        """打印结果"""
        print("\n快速健康检查结果:")
        print("-" * 40)

        checks = [
            ("配置文件", results.get("config_valid")),
            ("网络连接", results.get("network_ok")),
            ("浏览器状态", results.get("browser_ok")),
            ("登录状态", results.get("login_ok")),
        ]

        for name, status in checks:
            icon = "✅" if status else "❌"
            print(f"  {icon} {name}")

        if results.get("issues"):
            print("\n发现问题:")
            for issue in results["issues"]:
                print(f"  ⚠️ {issue}")

        print("-" * 40)
