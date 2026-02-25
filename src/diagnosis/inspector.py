"""
页面检查器
自动检查页面状态、发现问题、验证元素
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """问题严重程度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(Enum):
    """问题类型"""

    LOGIN_REQUIRED = "login_required"
    CAPTCHA_DETECTED = "captcha_detected"
    ACCOUNT_LOCKED = "account_locked"
    PAGE_CRASHED = "page_crashed"
    ELEMENT_NOT_FOUND = "element_not_found"
    SLOW_RESPONSE = "slow_response"
    NETWORK_ERROR = "network_error"
    UNEXPECTED_REDIRECT = "unexpected_redirect"
    RATE_LIMITED = "rate_limited"
    SESSION_EXPIRED = "session_expired"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN = "unknown"


@dataclass
class DetectedIssue:
    """检测到的问题"""

    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    url: str | None = None
    selector: str | None = None
    evidence: str | None = None
    suggestions: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: "")

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class PageInspector:
    """页面检查器"""

    def __init__(self):
        self.detected_issues: list[DetectedIssue] = []

        self.login_indicators = [
            "sign in",
            "log in",
            "登录",
            "登陆",
            "enter your email",
            "输入电子邮件",
            "create account",
            "注册",
        ]

        self.captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "verify you're human",
            "验证您是人类",
            "security check",
            "安全检查",
            "unusual activity",
            "异常活动",
            "puzzle",
            "拼图验证",
            "i'm not a robot",
            "我不是机器人",
        ]

        self.account_lock_indicators = [
            "account locked",
            "account suspended",
            "账号已锁定",
            "account disabled",
            "access denied",
            "访问被拒绝",
            "temporarily unavailable",
            "暂时不可用",
            "contact support",
            "联系支持",
        ]

        self.rate_limit_indicators = [
            "too many requests",
            "请求过多",
            "try again later",
            "稍后再试",
            "rate limit",
            "频率限制",
            "slow down",
            "放慢速度",
        ]

        self.error_indicators = [
            "error",
            "错误",
            "failed",
            "失败",
            "something went wrong",
            "出了点问题",
            "try again",
            "重试",
        ]

        logger.info("页面检查器初始化完成")

    async def inspect_page(self, page) -> list[DetectedIssue]:
        """
        全面检查页面

        Args:
            page: Playwright Page 对象

        Returns:
            检测到的问题列表
        """
        issues = []

        try:
            url = page.url

            issues.extend(await self.check_page_validity(page))
            issues.extend(await self.check_login_status(page))
            issues.extend(await self.check_captcha(page))
            issues.extend(await self.check_account_status(page))
            issues.extend(await self.check_rate_limiting(page))
            issues.extend(await self.check_errors(page))

            for issue in issues:
                issue.url = url
                self.detected_issues.append(issue)

            return issues

        except Exception as e:
            logger.error(f"页面检查失败: {e}")
            return [
                DetectedIssue(
                    issue_type=IssueType.UNKNOWN,
                    severity=IssueSeverity.ERROR,
                    title="页面检查失败",
                    description="页面检查过程中发生错误，请查看日志了解详情",
                )
            ]

    async def check_page_validity(self, page) -> list[DetectedIssue]:
        """检查页面有效性"""
        issues = []

        try:
            if page.is_closed():
                issues.append(
                    DetectedIssue(
                        issue_type=IssueType.PAGE_CRASHED,
                        severity=IssueSeverity.CRITICAL,
                        title="页面已关闭",
                        description="页面已被关闭，无法继续操作",
                        suggestions=["重新创建页面上下文", "检查浏览器状态"],
                    )
                )
                return issues

            try:
                ready_state = await page.evaluate("() => document.readyState")
                if ready_state == "uninitialized":
                    issues.append(
                        DetectedIssue(
                            issue_type=IssueType.PAGE_CRASHED,
                            severity=IssueSeverity.WARNING,
                            title="页面未完全加载",
                            description=f"页面状态: {ready_state}",
                            suggestions=["等待页面加载完成", "刷新页面"],
                        )
                    )
            except Exception:
                issues.append(
                    DetectedIssue(
                        issue_type=IssueType.PAGE_CRASHED,
                        severity=IssueSeverity.ERROR,
                        title="页面状态检查失败",
                        description="无法获取页面状态，可能已崩溃",
                        suggestions=["重建页面上下文", "检查内存使用"],
                    )
                )

        except Exception as e:
            logger.debug(f"页面有效性检查异常: {e}")

        return issues

    async def check_login_status(self, page) -> list[DetectedIssue]:
        """检查登录状态"""
        issues = []

        try:
            content = await page.content()
            content_lower = content.lower()
            url = page.url.lower()

            if any(indicator in content_lower for indicator in self.login_indicators):
                if "rewards.microsoft.com" in url or "bing.com" in url:
                    login_url_patterns = ["login", "signin", "oauth", "authenticate"]
                    if any(pattern in url for pattern in login_url_patterns):
                        issues.append(
                            DetectedIssue(
                                issue_type=IssueType.LOGIN_REQUIRED,
                                severity=IssueSeverity.WARNING,
                                title="需要登录",
                                description="检测到登录页面，需要重新登录",
                                evidence=f"URL: {page.url}",
                                suggestions=[
                                    "检查会话状态文件是否存在",
                                    "尝试自动登录",
                                    "等待手动登录",
                                ],
                            )
                        )

        except Exception as e:
            logger.debug(f"登录状态检查异常: {e}")

        return issues

    async def check_captcha(self, page) -> list[DetectedIssue]:
        """检查验证码"""
        issues = []

        try:
            content = await page.content()
            content_lower = content.lower()
            url = page.url.lower()

            if any(keyword in url for keyword in ["login", "signin", "search", "bing.com"]):
                captcha_selectors = [
                    "iframe[src*='captcha']",
                    "iframe[src*='recaptcha']",
                    ".g-recaptcha",
                    ".h-captcha",
                    "#captcha-container",
                    "[data-sitekey]",
                    "[class*='captcha']",
                ]

                for selector in captcha_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        try:
                            is_visible = await element.is_visible()
                            if is_visible:
                                issues.append(
                                    DetectedIssue(
                                        issue_type=IssueType.CAPTCHA_DETECTED,
                                        severity=IssueSeverity.CRITICAL,
                                        title="检测到验证码元素",
                                        description=f"发现验证码元素: {selector}",
                                        selector=selector,
                                        suggestions=["需要人工处理验证码"],
                                    )
                                )
                                break
                        except Exception:
                            pass

            if "captcha" in content_lower or "recaptcha" in content_lower:
                has_captcha_element = False
                for selector in ["iframe[src*='captcha']", "[class*='captcha']"]:
                    element = await page.query_selector(selector)
                    if element:
                        has_captcha_element = True
                        break

                if has_captcha_element:
                    issues.append(
                        DetectedIssue(
                            issue_type=IssueType.CAPTCHA_DETECTED,
                            severity=IssueSeverity.CRITICAL,
                            title="检测到验证码",
                            description="发现验证码相关内容",
                            suggestions=[
                                "暂停自动操作",
                                "等待人工处理验证码",
                                "降低操作频率以避免触发",
                            ],
                        )
                    )

        except Exception as e:
            logger.debug(f"验证码检查异常: {e}")

        return issues

    async def check_account_status(self, page) -> list[DetectedIssue]:
        """检查账户状态"""
        issues = []

        try:
            content = await page.content()
            content_lower = content.lower()

            for indicator in self.account_lock_indicators:
                if indicator in content_lower:
                    issues.append(
                        DetectedIssue(
                            issue_type=IssueType.ACCOUNT_LOCKED,
                            severity=IssueSeverity.CRITICAL,
                            title="账户可能被锁定",
                            description=f"发现锁定指示器: '{indicator}'",
                            evidence=indicator,
                            suggestions=["停止所有自动操作", "检查账户状态", "联系Microsoft支持"],
                        )
                    )
                    break

        except Exception as e:
            logger.debug(f"账户状态检查异常: {e}")

        return issues

    async def check_rate_limiting(self, page) -> list[DetectedIssue]:
        """检查频率限制"""
        issues = []

        try:
            content = await page.content()
            content_lower = content.lower()
            url = page.url.lower()

            if any(keyword in url for keyword in ["login", "signin", "search", "bing.com"]):
                for indicator in self.rate_limit_indicators:
                    if indicator in content_lower:
                        is_visible = False
                        try:
                            elements = await page.query_selector_all("body *")
                            for element in elements:
                                try:
                                    text = await element.inner_text()
                                    if indicator.lower() in text.lower():
                                        is_displayed = await element.is_visible()
                                        if is_displayed:
                                            is_visible = True
                                            break
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        if is_visible:
                            issues.append(
                                DetectedIssue(
                                    issue_type=IssueType.RATE_LIMITED,
                                    severity=IssueSeverity.WARNING,
                                    title="检测到频率限制",
                                    description=f"发现限制指示器: '{indicator}'",
                                    evidence=indicator,
                                    suggestions=[
                                        "增加操作间隔时间",
                                        "暂停一段时间后重试",
                                        "降低自动化速度",
                                    ],
                                )
                            )
                            break

        except Exception as e:
            logger.debug(f"频率限制检查异常: {e}")

        return issues

    async def check_errors(self, page) -> list[DetectedIssue]:
        """检查页面错误"""
        issues = []

        try:
            content = await page.content()
            content.lower()

            error_indicators = [
                "error",
                "错误",
                "failed",
                "失败",
                "something went wrong",
                "出了点问题",
                "try again",
                "重试",
            ]

            visible_error_elements = []
            error_selectors = [
                ".error",
                ".alert-danger",
                ".alert-error",
                "[class*='error']",
                "[class*='alert']",
                "#error",
                "[id*='error']",
            ]

            for selector in error_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        is_visible = await element.is_visible()
                        if is_visible:
                            text = await element.inner_text()
                            if any(indicator in text.lower() for indicator in error_indicators):
                                visible_error_elements.append(text)
                    except Exception:
                        pass

            if len(visible_error_elements) >= 2:
                issues.append(
                    DetectedIssue(
                        issue_type=IssueType.VALIDATION_ERROR,
                        severity=IssueSeverity.WARNING,
                        title="页面包含错误",
                        description=f"发现 {len(visible_error_elements)} 个可见错误元素",
                        suggestions=["检查网络连接", "刷新页面", "查看详细日志"],
                    )
                )

        except Exception as e:
            logger.debug(f"错误检查异常: {e}")

        return issues

    async def verify_element(
        self, page, selector: str, timeout: int = 5000
    ) -> tuple[bool, DetectedIssue | None]:
        """
        验证元素是否存在

        Args:
            page: Playwright Page 对象
            selector: 元素选择器
            timeout: 超时时间(毫秒)

        Returns:
            (是否找到, 问题对象)
        """
        try:
            element = await page.wait_for_selector(selector, timeout=timeout, state="visible")

            if element:
                return True, None
            else:
                issue = DetectedIssue(
                    issue_type=IssueType.ELEMENT_NOT_FOUND,
                    severity=IssueSeverity.WARNING,
                    title="元素未找到",
                    description=f"选择器: {selector}",
                    selector=selector,
                    suggestions=["检查选择器是否正确", "页面结构可能已变化", "等待页面完全加载"],
                )
                self.detected_issues.append(issue)
                return False, issue

        except Exception as e:
            issue = DetectedIssue(
                issue_type=IssueType.ELEMENT_NOT_FOUND,
                severity=IssueSeverity.WARNING,
                title="元素查找超时",
                description=f"选择器: {selector}, 错误: {str(e)}",
                selector=selector,
                suggestions=["增加等待时间", "检查选择器语法"],
            )
            self.detected_issues.append(issue)
            return False, issue

    async def verify_elements_batch(
        self, page, selectors: dict[str, str]
    ) -> dict[str, tuple[bool, DetectedIssue | None]]:
        """
        批量验证元素

        Args:
            page: Playwright Page 对象
            selectors: {名称: 选择器} 字典

        Returns:
            {名称: (是否找到, 问题对象)} 字典
        """
        results = {}

        for name, selector in selectors.items():
            found, issue = await self.verify_element(page, selector, timeout=3000)
            results[name] = (found, issue)

        return results

    def get_critical_issues(self) -> list[DetectedIssue]:
        """获取所有严重问题"""
        return [
            issue
            for issue in self.detected_issues
            if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]
        ]

    def get_all_issues(self) -> list[DetectedIssue]:
        """获取所有问题"""
        return self.detected_issues

    def clear_issues(self):
        """清空问题列表"""
        self.detected_issues.clear()

    def get_issue_summary(self) -> dict[str, Any]:
        """获取问题摘要"""
        severity_counts = {}
        type_counts = {}

        for issue in self.detected_issues:
            sev = issue.severity.value
            typ = issue.issue_type.value

            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            type_counts[typ] = type_counts.get(typ, 0) + 1

        return {
            "total_issues": len(self.detected_issues),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "critical_count": len(self.get_critical_issues()),
        }

    def _map_exception_to_issue_type(self, error: Exception) -> IssueType:
        """将异常映射到问题类型"""
        error_str = str(error).lower()
        error_type = type(error).__name__

        if "timeout" in error_str or "timeout" in error_type.lower():
            return IssueType.SLOW_RESPONSE

        if "network" in error_str or "connection" in error_str:
            return IssueType.NETWORK_ERROR

        if "selector" in error_str or "element" in error_str:
            return IssueType.ELEMENT_NOT_FOUND

        if "navigation" in error_str or "redirect" in error_str:
            return IssueType.UNEXPECTED_REDIRECT

        if "crash" in error_str or "closed" in error_str:
            return IssueType.PAGE_CRASHED

        return IssueType.UNKNOWN
