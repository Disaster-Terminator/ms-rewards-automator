"""
诊断目录轮转清理
保留最近的 N 次诊断记录，删除旧记录
"""

import logging
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_DIAGNOSIS_FOLDERS = 10
MAX_AGE_DAYS = 7


def _get_dir_size(dir_path: Path) -> int:
    """
    计算目录的总大小（字节）

    Args:
        dir_path: 目录路径

    Returns:
        目录总大小（字节）
    """
    total_size = 0
    try:
        for item in dir_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except Exception as e:
        logger.warning(f"计算目录大小时出错 {dir_path}: {e}")
    return total_size


def cleanup_old_diagnoses(
    logs_dir: Path,
    max_folders: int = MAX_DIAGNOSIS_FOLDERS,
    max_age_days: int = MAX_AGE_DAYS,
    dry_run: bool = False,
) -> dict:
    """
    清理旧的诊断目录，保留最近的 N 个或不超过最大天数的

    Args:
        logs_dir: logs 目录路径
        max_folders: 最多保留的文件夹数量
        max_age_days: 最大保留天数
        dry_run: 若为 True，仅模拟删除不实际删除

    Returns:
        清理结果统计，包含 deleted, skipped, errors, total_size_freed 字段
    """
    diagnosis_dir = logs_dir / "diagnosis"
    if not diagnosis_dir.exists():
        return {"deleted": 0, "skipped": 0, "errors": 0, "total_size_freed": 0}

    folders = sorted(diagnosis_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

    result = {"deleted": 0, "skipped": 0, "errors": 0, "total_size_freed": 0}
    age_threshold = max_age_days * 24 * 60 * 60

    for i, folder in enumerate(folders):
        if not folder.is_dir():
            continue

        try:
            folder_age = time.time() - folder.stat().st_mtime

            should_delete = (i >= max_folders) or (folder_age > age_threshold)

            if should_delete:
                if dry_run:
                    logger.debug(f"[dry_run] 将删除旧诊断目录: {folder}")
                    result["deleted"] += 1
                else:
                    folder_size = _get_dir_size(folder)
                    shutil.rmtree(folder)
                    logger.debug(f"已清理旧诊断目录: {folder}")
                    result["deleted"] += 1
                    result["total_size_freed"] += folder_size
            else:
                result["skipped"] += 1
        except Exception as e:
            logger.warning(f"清理诊断目录失败 {folder}: {e}")
            result["errors"] += 1

    if result["deleted"] > 0:
        logger.info(f"诊断目录清理完成: 删除 {result['deleted']} 个旧目录")

    return result
