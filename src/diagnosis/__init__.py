"""
诊断模块
提供轻量级诊断能力，集成到 --dev/--user 模式
"""

from pathlib import Path

from .engine import DiagnosisCategory, DiagnosisResult, DiagnosticEngine
from .inspector import DetectedIssue, IssueSeverity, IssueType, PageInspector
from .reporter import DiagnosisReporter
from .screenshot import ScreenshotManager


# 向后兼容：提供 cleanup_old_diagnoses 函数
def cleanup_old_diagnoses(
    logs_dir: Path, max_folders: int = 10, max_age_days: int = 7, dry_run: bool = False
) -> dict:
    """
    清理旧的诊断文件夹（向后兼容接口）

    Args:
        logs_dir: 日志目录路径
        max_folders: 保留的最大文件夹数量
        max_age_days: 文件夹最大保留天数
        dry_run: 是否为模拟运行

    Returns:
        清理统计信息
    """
    # 延迟导入以避免顶层导入失败影响诊断包可用性
    from infrastructure.log_rotation import LogRotation

    return LogRotation().cleanup_old_diagnoses(logs_dir, max_folders, max_age_days, dry_run)


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
    "cleanup_old_diagnoses",
]
