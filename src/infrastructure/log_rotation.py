"""
日志和截图轮替管理模块
自动清理过期的日志和截图文件
"""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class LogRotation:
    """日志和截图轮替管理器"""

    def __init__(
        self,
        logs_dir: str = "logs",
        screenshots_dir: str = "screenshots",
        max_age_days: int = 7,
        keep_min_files: int = 10,
    ):
        """
        初始化轮替管理器

        Args:
            logs_dir: 日志目录
            screenshots_dir: 截图目录
            max_age_days: 最大保留天数
            keep_min_files: 最少保留文件数量
        """
        self.logs_dir = Path(logs_dir)
        self.screenshots_dir = Path(screenshots_dir)
        self.max_age_days = max_age_days
        self.keep_min_files = keep_min_files

        # 计算时间阈值（秒）
        self.age_threshold = max_age_days * 24 * 60 * 60

    def should_delete(self, file_path: Path, min_age_hours: int = 1) -> bool:
        """
        判断文件是否应该删除

        Args:
            file_path: 文件路径
            min_age_hours: 最小年龄（小时），文件至少存在这么久才会被删除

        Returns:
            是否应该删除
        """
        try:
            # 获取文件修改时间
            mtime = file_path.stat().st_mtime
            age = time.time() - mtime

            # 保护新文件：至少存在 min_age_hours 小时才考虑删除
            min_age_seconds = min_age_hours * 60 * 60
            if age < min_age_seconds:
                return False

            # 如果超过最大天数，应该删除
            if age > self.age_threshold:
                return True

            return False
        except Exception:
            return False

    def cleanup_directory(
        self, directory: Path, patterns: list | None = None, dry_run: bool = False
    ) -> dict:
        """
        清理目录中的过期文件

        Args:
            directory: 目录路径
            patterns: 文件模式列表（如 ["*.log", "*.html"]）
            dry_run: 是否仅模拟运行

        Returns:
            清理结果统计
        """
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return {"deleted": 0, "errors": 0, "skipped": 0}

        result: dict[str, int] = {"deleted": 0, "errors": 0, "skipped": 0, "total_size_freed": 0}

        files: list[Path] = []
        if patterns:
            for pattern in patterns:
                files.extend(directory.glob(pattern))
        else:
            files = [f for f in directory.iterdir() if f.is_file()]

        # 按修改时间排序（旧的在前）
        files.sort(key=lambda x: x.stat().st_mtime)

        # 计算应该保留的文件数
        files_to_keep = max(len(files) - self.keep_min_files, 0)

        for i, file_path in enumerate(files):
            try:
                # 如果还有足够的文件保留，跳过
                if i < files_to_keep and not self.should_delete(file_path):
                    result["skipped"] += 1
                    continue

                # 检查是否应该删除（必须通过 should_delete 检查）
                if self.should_delete(file_path):
                    file_size = file_path.stat().st_size

                    if not dry_run:
                        file_path.unlink()
                        logger.debug(f"已删除: {file_path.name}")

                    result["deleted"] += 1
                    result["total_size_freed"] += file_size
                else:
                    result["skipped"] += 1

            except Exception as e:
                logger.error(f"删除文件失败 {file_path}: {e}")
                result["errors"] += 1

        return result

    def cleanup_all(self, dry_run: bool = False) -> dict:
        """
        清理所有日志和截图

        Args:
            dry_run: 是否仅模拟运行

        Returns:
            总体清理结果
        """
        total_result: dict[str, dict[str, int]] = {
            "logs": {},
            "screenshots": {},
            "diagnosis": {},
        }

        # 1. 清理主日志文件（保留最近的）
        if self.logs_dir.exists():
            main_log = self.logs_dir / "automator.log"
            if main_log.exists():
                try:
                    with open(main_log, encoding="utf-8") as f:
                        lines = f.readlines()

                    if len(lines) > 10000:
                        with open(main_log, "w", encoding="utf-8") as f:
                            f.writelines(lines[-10000:])
                        logger.info(f"日志轮替: {len(lines)} → 10000 行")
                except Exception as e:
                    logger.error(f"日志轮替失败: {e}")

        # 2. 清理诊断目录（logs/diagnosis）
        diagnosis_dir = self.logs_dir / "diagnosis"
        if diagnosis_dir.exists():
            from diagnosis.rotation import cleanup_old_diagnoses

            diagnosis_result = cleanup_old_diagnoses(
                self.logs_dir, max_folders=10, max_age_days=self.max_age_days
            )
            total_result["diagnosis"] = diagnosis_result

        # 3. 清理 screenshots
        if self.screenshots_dir.exists():
            total_result["screenshots"] = self.cleanup_directory(
                self.screenshots_dir, patterns=["*.png", "*.jpg"], dry_run=dry_run
            )

        # 4. 清理其他日志文件
        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.name == "automator.log":
                    continue
                try:
                    if self.should_delete(log_file):
                        if not dry_run:
                            log_file.unlink()
                            logger.debug(f"已删除日志: {log_file.name}")
                        total_result["logs"]["deleted"] = total_result["logs"].get("deleted", 0) + 1
                except Exception as e:
                    logger.error(f"删除日志失败 {log_file}: {e}")

        # 输出汇总
        total_deleted = (
            total_result["diagnosis"].get("deleted", 0)
            + total_result["screenshots"].get("deleted", 0)
            + total_result["logs"].get("deleted", 0)
        )
        total_size = total_result["diagnosis"].get("total_size_freed", 0) + total_result[
            "screenshots"
        ].get("total_size_freed", 0)

        logger.info(
            f"清理完成: 删除 {total_deleted} 个文件，释放 {total_size / 1024 / 1024:.2f} MB"
        )

        return total_result


def cleanup_old_files(
    logs_dir: str = "logs", screenshots_dir: str = "screenshots", dry_run: bool = False
):
    """
    便捷函数：清理旧文件

    Args:
        logs_dir: 日志目录
        screenshots_dir: 截图目录
        dry_run: 是否仅模拟运行

    Returns:
        清理结果
    """
    rotator = LogRotation(logs_dir, screenshots_dir)
    return rotator.cleanup_all(dry_run=dry_run)


if __name__ == "__main__":
    # 测试运行
    logging.basicConfig(level=logging.INFO)
    result = cleanup_old_files(dry_run=False)
    print(f"清理结果: {result}")
