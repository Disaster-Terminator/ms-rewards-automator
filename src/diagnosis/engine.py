"""
诊断引擎
分析问题根因、生成解决方案、提供修复建议
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .inspector import DetectedIssue, IssueType

logger = logging.getLogger(__name__)


class DiagnosisCategory(Enum):
    """诊断类别"""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    BROWSER = "browser"
    SELECTOR = "selector"
    RATE_LIMITING = "rate_limiting"
    ACCOUNT = "account"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class DiagnosisResult:
    """诊断结果"""

    category: DiagnosisCategory
    root_cause: str
    confidence: float
    description: str
    affected_components: list[str] = field(default_factory=list)
    solutions: list[dict[str, Any]] = field(default_factory=list)
    related_issues: list[DetectedIssue] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: "")

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DiagnosticEngine:
    """诊断引擎"""

    def __init__(self):
        self.diagnoses: list[DiagnosisResult] = []
        self.issue_patterns = self._init_issue_patterns()
        self.solution_templates = self._init_solution_templates()

        logger.info("诊断引擎初始化完成")

    def _init_issue_patterns(self) -> dict[IssueType, dict[str, Any]]:
        """初始化问题模式"""
        return {
            IssueType.LOGIN_REQUIRED: {
                "category": DiagnosisCategory.AUTHENTICATION,
                "root_causes": [
                    "会话已过期",
                    "Cookie已失效",
                    "未正确保存登录状态",
                    "Microsoft强制重新登录",
                ],
                "confidence": 0.9,
            },
            IssueType.CAPTCHA_DETECTED: {
                "category": DiagnosisCategory.RATE_LIMITING,
                "root_causes": ["自动化行为被检测", "操作频率过高", "IP地址异常", "浏览器指纹异常"],
                "confidence": 0.85,
            },
            IssueType.ACCOUNT_LOCKED: {
                "category": DiagnosisCategory.ACCOUNT,
                "root_causes": [
                    "账户被Microsoft限制",
                    "异常活动检测",
                    "多次登录失败",
                    "违反服务条款",
                ],
                "confidence": 0.95,
            },
            IssueType.PAGE_CRASHED: {
                "category": DiagnosisCategory.BROWSER,
                "root_causes": ["内存不足", "浏览器进程异常", "页面资源加载失败", "JavaScript错误"],
                "confidence": 0.7,
            },
            IssueType.ELEMENT_NOT_FOUND: {
                "category": DiagnosisCategory.SELECTOR,
                "root_causes": [
                    "页面结构已变化",
                    "选择器已过时",
                    "页面未完全加载",
                    "动态内容未渲染",
                ],
                "confidence": 0.8,
            },
            IssueType.NETWORK_ERROR: {
                "category": DiagnosisCategory.NETWORK,
                "root_causes": ["网络连接不稳定", "DNS解析失败", "服务器无响应", "防火墙阻止"],
                "confidence": 0.75,
            },
            IssueType.RATE_LIMITED: {
                "category": DiagnosisCategory.RATE_LIMITING,
                "root_causes": ["请求频率过高", "短时间内大量操作", "触发反爬虫机制"],
                "confidence": 0.9,
            },
            IssueType.SESSION_EXPIRED: {
                "category": DiagnosisCategory.AUTHENTICATION,
                "root_causes": ["会话超时", "Cookie过期", "服务器端会话失效"],
                "confidence": 0.9,
            },
            IssueType.SLOW_RESPONSE: {
                "category": DiagnosisCategory.NETWORK,
                "root_causes": ["网络延迟高", "服务器负载高", "资源加载慢", "DNS解析慢"],
                "confidence": 0.6,
            },
            IssueType.VALIDATION_ERROR: {
                "category": DiagnosisCategory.CONFIGURATION,
                "root_causes": ["配置参数错误", "输入数据格式不正确", "业务逻辑验证失败"],
                "confidence": 0.7,
            },
        }

    def _init_solution_templates(self) -> dict[IssueType, list[dict[str, Any]]]:
        """初始化解决方案模板"""
        return {
            IssueType.LOGIN_REQUIRED: [
                {
                    "action": "check_session_file",
                    "description": "检查会话状态文件是否存在且有效",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "re_login",
                    "description": "重新执行登录流程",
                    "auto_fixable": True,
                    "priority": 2,
                },
                {
                    "action": "update_credentials",
                    "description": "更新登录凭据配置",
                    "auto_fixable": False,
                    "priority": 3,
                },
            ],
            IssueType.CAPTCHA_DETECTED: [
                {
                    "action": "pause_and_wait",
                    "description": "暂停自动化操作，等待人工处理",
                    "auto_fixable": False,
                    "priority": 1,
                },
                {
                    "action": "increase_delay",
                    "description": "增加操作间隔时间",
                    "auto_fixable": True,
                    "priority": 2,
                },
                {
                    "action": "enable_stealth_mode",
                    "description": "启用更隐蔽的自动化模式",
                    "auto_fixable": True,
                    "priority": 3,
                },
            ],
            IssueType.ACCOUNT_LOCKED: [
                {
                    "action": "stop_immediately",
                    "description": "立即停止所有自动化操作",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "manual_verification",
                    "description": "人工登录账户验证状态",
                    "auto_fixable": False,
                    "priority": 2,
                },
                {
                    "action": "contact_support",
                    "description": "联系Microsoft支持解锁账户",
                    "auto_fixable": False,
                    "priority": 3,
                },
            ],
            IssueType.PAGE_CRASHED: [
                {
                    "action": "recreate_context",
                    "description": "重新创建浏览器上下文",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "restart_browser",
                    "description": "重启浏览器进程",
                    "auto_fixable": True,
                    "priority": 2,
                },
                {
                    "action": "check_memory",
                    "description": "检查系统内存使用情况",
                    "auto_fixable": True,
                    "priority": 3,
                },
            ],
            IssueType.ELEMENT_NOT_FOUND: [
                {
                    "action": "wait_and_retry",
                    "description": "等待后重试查找元素",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "update_selector",
                    "description": "更新选择器以匹配新页面结构",
                    "auto_fixable": False,
                    "priority": 2,
                },
                {
                    "action": "use_alternative_selector",
                    "description": "使用备用选择器",
                    "auto_fixable": True,
                    "priority": 3,
                },
            ],
            IssueType.NETWORK_ERROR: [
                {
                    "action": "retry_with_backoff",
                    "description": "使用指数退避重试",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "check_network",
                    "description": "检查网络连接状态",
                    "auto_fixable": True,
                    "priority": 2,
                },
                {
                    "action": "change_dns",
                    "description": "更换DNS服务器",
                    "auto_fixable": False,
                    "priority": 3,
                },
            ],
            IssueType.RATE_LIMITED: [
                {
                    "action": "increase_interval",
                    "description": "增加操作间隔时间",
                    "auto_fixable": True,
                    "priority": 1,
                },
                {
                    "action": "pause_execution",
                    "description": "暂停执行一段时间",
                    "auto_fixable": True,
                    "priority": 2,
                },
                {
                    "action": "reduce_batch_size",
                    "description": "减少批量操作数量",
                    "auto_fixable": True,
                    "priority": 3,
                },
            ],
        }

    def diagnose(
        self, issues: list[DetectedIssue], context: dict[str, Any] | None = None
    ) -> list[DiagnosisResult]:
        """
        诊断问题

        Args:
            issues: 检测到的问题列表
            context: 额外上下文信息

        Returns:
            诊断结果列表
        """
        diagnoses = []
        context = context or {}

        for issue in issues:
            pattern = self.issue_patterns.get(issue.issue_type)

            if pattern:
                solutions = self._get_solutions(issue.issue_type, context)

                diagnosis = DiagnosisResult(
                    category=pattern["category"],
                    root_cause=self._determine_root_cause(pattern["root_causes"], issue, context),
                    confidence=pattern["confidence"],
                    description=self._generate_description(issue, pattern),
                    affected_components=self._get_affected_components(issue),
                    solutions=solutions,
                    related_issues=[issue],
                )

                diagnoses.append(diagnosis)
                self.diagnoses.append(diagnosis)

        diagnoses.extend(self._cross_analyze(issues, context))

        return diagnoses

    def _get_solutions(
        self, issue_type: IssueType, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """获取解决方案"""
        templates = self.solution_templates.get(issue_type, [])

        solutions = []
        for template in templates:
            solution = template.copy()
            solution["applicable"] = self._check_solution_applicability(template, context)
            solutions.append(solution)

        return solutions

    def _determine_root_cause(
        self, possible_causes: list[str], issue: DetectedIssue, context: dict[str, Any]
    ) -> str:
        """确定根本原因"""
        if not possible_causes:
            return "未知原因"

        if context.get("network_unstable"):
            for cause in possible_causes:
                if "网络" in cause or "连接" in cause:
                    return cause

        if context.get("high_frequency"):
            for cause in possible_causes:
                if "频率" in cause or "过高" in cause:
                    return cause

        return possible_causes[0]

    def _generate_description(self, issue: DetectedIssue, pattern: dict[str, Any]) -> str:
        """生成诊断描述"""
        category_names = {
            DiagnosisCategory.AUTHENTICATION: "认证问题",
            DiagnosisCategory.NETWORK: "网络问题",
            DiagnosisCategory.BROWSER: "浏览器问题",
            DiagnosisCategory.SELECTOR: "选择器问题",
            DiagnosisCategory.RATE_LIMITING: "频率限制",
            DiagnosisCategory.ACCOUNT: "账户问题",
            DiagnosisCategory.CONFIGURATION: "配置问题",
            DiagnosisCategory.SYSTEM: "系统问题",
            DiagnosisCategory.UNKNOWN: "未知问题",
        }

        category_name = category_names.get(pattern["category"], "其他问题")

        return f"[{category_name}] {issue.title}: {issue.description}"

    def _get_affected_components(self, issue: DetectedIssue) -> list[str]:
        """获取受影响的组件"""

        type_to_component = {
            IssueType.LOGIN_REQUIRED: ["auth", "session"],
            IssueType.CAPTCHA_DETECTED: ["browser", "anti-ban"],
            IssueType.ACCOUNT_LOCKED: ["account"],
            IssueType.PAGE_CRASHED: ["browser"],
            IssueType.ELEMENT_NOT_FOUND: ["selector", "ui"],
            IssueType.NETWORK_ERROR: ["network"],
            IssueType.RATE_LIMITED: ["anti-ban", "scheduler"],
            IssueType.SESSION_EXPIRED: ["auth", "session"],
            IssueType.SLOW_RESPONSE: ["network"],
            IssueType.VALIDATION_ERROR: ["config"],
        }

        return type_to_component.get(issue.issue_type, ["unknown"])

    def _check_solution_applicability(
        self, solution: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """检查解决方案是否适用"""
        if not solution.get("auto_fixable", False):
            return False

        return True

    def _cross_analyze(
        self, issues: list[DetectedIssue], context: dict[str, Any]
    ) -> list[DiagnosisResult]:
        """交叉分析多个问题"""
        additional_diagnoses = []

        if len(issues) >= 3:
            categories = set()
            for issue in issues:
                pattern = self.issue_patterns.get(issue.issue_type)
                if pattern:
                    categories.add(pattern["category"])

            if len(categories) >= 3:
                additional_diagnoses.append(
                    DiagnosisResult(
                        category=DiagnosisCategory.SYSTEM,
                        root_cause="多个组件同时出现问题，可能是系统性问题",
                        confidence=0.6,
                        description="检测到多个不同类型的问题，建议全面检查系统状态",
                        affected_components=list(categories),
                        solutions=[
                            {
                                "action": "full_system_check",
                                "description": "执行全面系统检查",
                                "auto_fixable": True,
                                "priority": 1,
                            }
                        ],
                    )
                )

        login_issues = [i for i in issues if i.issue_type == IssueType.LOGIN_REQUIRED]
        captcha_issues = [i for i in issues if i.issue_type == IssueType.CAPTCHA_DETECTED]

        if login_issues and captcha_issues:
            additional_diagnoses.append(
                DiagnosisResult(
                    category=DiagnosisCategory.AUTHENTICATION,
                    root_cause="登录问题触发验证码，可能是自动化行为被检测",
                    confidence=0.8,
                    description="同时检测到登录问题和验证码，建议暂停自动化操作",
                    affected_components=["auth", "anti-ban"],
                    solutions=[
                        {
                            "action": "pause_and_verify",
                            "description": "暂停自动化，人工验证账户状态",
                            "auto_fixable": False,
                            "priority": 1,
                        }
                    ],
                )
            )

        return additional_diagnoses

    def get_auto_fixable_solutions(self) -> list[dict[str, Any]]:
        """获取可自动修复的解决方案"""
        solutions = []

        for diagnosis in self.diagnoses:
            for solution in diagnosis.solutions:
                if solution.get("applicable") and solution.get("auto_fixable"):
                    solutions.append({"diagnosis": diagnosis, "solution": solution})

        solutions.sort(key=lambda x: x["solution"].get("priority", 999))

        return solutions

    def get_critical_diagnoses(self) -> list[DiagnosisResult]:
        """获取严重诊断结果"""
        critical_categories = [DiagnosisCategory.ACCOUNT, DiagnosisCategory.AUTHENTICATION]

        return [
            d for d in self.diagnoses if d.category in critical_categories or d.confidence >= 0.9
        ]

    def save_diagnosis_report(self, filepath: str = "logs/diagnosis_report.json"):
        """保存诊断报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_diagnoses": len(self.diagnoses),
            "diagnoses": [
                {
                    "category": d.category.value,
                    "root_cause": d.root_cause,
                    "confidence": d.confidence,
                    "description": d.description,
                    "affected_components": d.affected_components,
                    "solutions": d.solutions,
                    "timestamp": d.timestamp,
                }
                for d in self.diagnoses
            ],
            "auto_fixable_count": len(self.get_auto_fixable_solutions()),
            "critical_count": len(self.get_critical_diagnoses()),
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"诊断报告已保存: {filepath}")

    def quick_check(self, page, check_type: str) -> "QuickDiagnosis":
        """
        快速诊断检查

        Args:
            page: Playwright 页面对象
            check_type: 检查类型 (login/search/task/summary)

        Returns:
            QuickDiagnosis: 简化的诊断结果
        """
        from .inspector import PageInspector

        inspector = PageInspector()
        issues = []

        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():

                async def check():
                    return await inspector.inspect_page(page)

                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, check())
                    issues = future.result()
            else:
                issues = asyncio.run(inspector.inspect_page(page))
        except Exception as e:
            logger.error(f"快速检查失败: {e}")
            from .inspector import IssueSeverity, IssueType

            return QuickDiagnosis(
                check_type=check_type,
                issues=[
                    DetectedIssue(
                        issue_type=IssueType.UNKNOWN,
                        severity=IssueSeverity.ERROR,
                        title="诊断检查执行失败",
                        description=f"诊断检查执行失败: {str(e)}",
                        suggestions=["请检查日志获取详细信息"],
                    )
                ],
                has_critical=True,
                summary=f"{check_type} 检查失败，请查看日志",
            )

        critical = any(i.severity.value in ["critical", "error"] for i in issues)

        return QuickDiagnosis(
            check_type=check_type,
            issues=issues,
            has_critical=critical,
            summary=self._generate_quick_summary(issues, check_type),
        )

    def _generate_quick_summary(self, issues: list, check_type: str) -> str:
        """生成快速摘要"""
        if not issues:
            return f"{check_type} 检查通过"

        critical_count = sum(1 for i in issues if i.severity.value in ["critical", "error"])
        warning_count = sum(1 for i in issues if i.severity.value == "warning")

        parts = []
        if critical_count > 0:
            parts.append(f"{critical_count} 个严重问题")
        if warning_count > 0:
            parts.append(f"{warning_count} 个警告")

        return f"{check_type} 发现: {', '.join(parts)}"


@dataclass
class QuickDiagnosis:
    """快速诊断结果"""

    check_type: str
    issues: list[DetectedIssue]
    has_critical: bool
    summary: str
