"""
诊断模块
提供轻量级诊断能力，集成到 --dev/--user 模式
"""

from .engine import DiagnosisCategory, DiagnosisResult, DiagnosticEngine
from .inspector import DetectedIssue, IssueSeverity, IssueType, PageInspector
from .reporter import DiagnosisReporter
from .screenshot import ScreenshotManager

__all__ = [
    "DiagnosticEngine",
    "DiagnosisCategory",
    "DiagnosisResult",
    "PageInspector",
    "DetectedIssue",
    "IssueSeverity",
    "IssueType",
    "ScreenshotManager",
    "DiagnosisReporter",
]
