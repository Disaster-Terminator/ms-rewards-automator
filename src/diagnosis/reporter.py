"""
诊断报告生成器
生成简洁的中文摘要报告
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .engine import DiagnosticEngine
from .inspector import DetectedIssue, IssueSeverity

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisCheckpoint:
    """诊断检查点记录"""

    name: str
    timestamp: str
    issues: list[DetectedIssue] = field(default_factory=list)
    success: bool = True


class DiagnosisReporter:
    """诊断报告生成器"""

    def __init__(self, output_dir: str = "logs/diagnosis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        self.session_id = now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond:06d}"
        self.session_dir = self.output_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoints: list[DiagnosisCheckpoint] = []
        self.engine = DiagnosticEngine()

    def add_checkpoint(self, name: str, issues: list[DetectedIssue], success: bool = True):
        """添加检查点记录"""
        checkpoint = DiagnosisCheckpoint(
            name=name,
            timestamp=datetime.now().isoformat(),
            issues=issues,
            success=success,
        )
        self.checkpoints.append(checkpoint)

        if issues:
            self.engine.diagnose(issues)

    def generate_summary(self) -> str:
        """生成中文摘要报告"""
        lines = []
        lines.append("═" * 67)
        lines.append(
            f"                    诊断摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        )
        lines.append("═" * 67)
        lines.append("")

        lines.append("执行概况：")
        for cp in self.checkpoints:
            status = "✓" if cp.success else "✗"
            issue_count = len(cp.issues)
            if issue_count == 0:
                lines.append(f"  • {cp.name}: {status}")
            else:
                critical = sum(
                    1
                    for i in cp.issues
                    if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]
                )
                if critical > 0:
                    lines.append(f"  • {cp.name}: {status} ({critical} 个严重问题)")
                else:
                    lines.append(f"  • {cp.name}: {status} ({issue_count} 个警告)")

        all_issues = []
        for cp in self.checkpoints:
            all_issues.extend(cp.issues)

        if all_issues:
            lines.append("")
            lines.append("发现问题：")

            critical_issues = [
                i for i in all_issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]
            ]
            warning_issues = [i for i in all_issues if i.severity == IssueSeverity.WARNING]
            info_issues = [i for i in all_issues if i.severity == IssueSeverity.INFO]

            for issue in critical_issues:
                lines.append(f"  🔴 [{issue.issue_type.value}] {issue.title}")
                lines.append(f"     → {issue.description}")
                if issue.suggestions:
                    lines.append(f"     → 建议：{issue.suggestions[0]}")

            for issue in warning_issues:
                lines.append(f"  ⚠️ [{issue.issue_type.value}] {issue.title}")
                lines.append(f"     → {issue.description}")
                if issue.suggestions:
                    lines.append(f"     → 建议：{issue.suggestions[0]}")

            for issue in info_issues:
                lines.append(f"  ℹ️ [{issue.issue_type.value}] {issue.title}")
                lines.append(f"     → {issue.description}")

        lines.append("")

        summary_path = self.session_dir / "summary.txt"
        lines.append(f"诊断报告已保存：{summary_path}")
        lines.append("")
        lines.append("═" * 67)

        return "\n".join(lines)

    def save_summary(self) -> str:
        """保存摘要报告到文件"""
        summary = self.generate_summary()
        summary_path = self.session_dir / "summary.txt"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        logger.info(f"诊断摘要已保存: {summary_path}")
        return str(summary_path)

    def print_summary(self):
        """打印摘要报告到控制台"""
        print(self.generate_summary())

    def has_critical_issues(self) -> bool:
        """检查是否有严重问题"""
        for cp in self.checkpoints:
            for issue in cp.issues:
                if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]:
                    return True
        return False

    def get_session_dir(self) -> Path:
        """获取会话目录"""
        return self.session_dir
