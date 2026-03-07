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
    description: str
    affected_components: list[str] = field(default_factory=list)
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
            },
            IssueType.CAPTCHA_DETECTED: {
                "category": DiagnosisCategory.RATE_LIMITING,
                "root_causes": ["自动化行为被检测", "操作频率过高", "IP地址异常", "浏览器指纹异常"],
            },
            IssueType.ACCOUNT_LOCKED: {
                "category": DiagnosisCategory.ACCOUNT,
                "root_causes": [
                    "账户被Microsoft限制",
                    "异常活动检测",
                    "多次登录失败",
                    "违反服务条款",
                ],
            },
            IssueType.PAGE_CRASHED: {
                "category": DiagnosisCategory.BROWSER,
                "root_causes": ["内存不足", "浏览器进程异常", "页面资源加载失败", "JavaScript错误"],
            },
            IssueType.ELEMENT_NOT_FOUND: {
                "category": DiagnosisCategory.SELECTOR,
                "root_causes": [
                    "页面结构已变化",
                    "选择器已过时",
                    "页面未完全加载",
                    "动态内容未渲染",
                ],
            },
            IssueType.NETWORK_ERROR: {
                "category": DiagnosisCategory.NETWORK,
                "root_causes": ["网络连接不稳定", "DNS解析失败", "服务器无响应", "防火墙阻止"],
            },
            IssueType.RATE_LIMITED: {
                "category": DiagnosisCategory.RATE_LIMITING,
                "root_causes": ["请求频率过高", "短时间内大量操作", "触发反爬虫机制"],
            },
            IssueType.SESSION_EXPIRED: {
                "category": DiagnosisCategory.AUTHENTICATION,
                "root_causes": ["会话超时", "Cookie过期", "服务器端会话失效"],
            },
            IssueType.SLOW_RESPONSE: {
                "category": DiagnosisCategory.NETWORK,
                "root_causes": ["网络延迟高", "服务器负载高", "资源加载慢", "DNS解析慢"],
            },
            IssueType.VALIDATION_ERROR: {
                "category": DiagnosisCategory.CONFIGURATION,
                "root_causes": ["配置参数错误", "输入数据格式不正确", "业务逻辑验证失败"],
            },
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
                diagnosis = DiagnosisResult(
                    category=pattern["category"],
                    root_cause=self._determine_root_cause(pattern["root_causes"], issue, context),
                    description=self._generate_description(issue, pattern),
                    affected_components=self._get_affected_components(issue),
                    related_issues=[issue],
                )

                diagnoses.append(diagnosis)
                self.diagnoses.append(diagnosis)

        return diagnoses

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

    def save_diagnosis_report(self, filepath: str = "logs/diagnosis_report.json"):
        """保存诊断报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_diagnoses": len(self.diagnoses),
            "diagnoses": [
                {
                    "category": d.category.value,
                    "root_cause": d.root_cause,
                    "description": d.description,
                    "affected_components": d.affected_components,
                    "timestamp": d.timestamp,
                }
                for d in self.diagnoses
            ],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"诊断报告已保存: {filepath}")

    async def quick_check(self, page, check_type: str) -> "QuickDiagnosis":
        """
        快速诊断检查（异步版本）

        Args:
            page: Playwright 页面对象
            check_type: 检查类型 (login/search/task/summary)

        Returns:
            QuickDiagnosis: 简化的诊断结果
        """
        from .inspector import PageInspector

        inspector = PageInspector()
        issues = []

        try:
            issues = await inspector.inspect_page(page)
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
