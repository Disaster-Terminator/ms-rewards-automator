import logging
from datetime import datetime
from pathlib import Path

from filelock import FileLock
from tinydb import Query, TinyDB

from .models import IssueCommentOverview, ReviewMetadata, ReviewOverview, ReviewThreadState

logger = logging.getLogger(__name__)


class ReviewManager:
    """
    评论状态管理器 - 使用 TinyDB 进行持久化 + FileLock 确保并发安全
    """

    def __init__(self, db_path: str = ".trae/data/review_threads.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.lock_path = self.db_path.with_suffix(".lock")

        self.db = TinyDB(self.db_path)
        self.Thread = Query()
        self.Metadata = Query()
        self.Overview = Query()

    def save_threads(self, threads: list[ReviewThreadState], metadata: ReviewMetadata) -> None:
        """
        全量保存/更新线程状态

        实现远端状态强同步：
        - 如果 GitHub 上 isResolved=true，强制更新本地 local_status 为 resolved
        - 标记 resolution_type 为 manual_on_github
        - 更新 enriched_context（从 Prompt 映射或 Qodo 解析）
        """
        with FileLock(self.lock_path):
            meta_table = self.db.table("metadata")
            meta_table.truncate()
            meta_table.insert(metadata.model_dump())

            thread_table = self.db.table("threads")

            for thread in threads:
                existing = thread_table.get(self.Thread.id == thread.id)

                if existing:
                    update_data = {
                        "is_resolved": thread.is_resolved,
                        "last_updated": datetime.utcnow().isoformat(),
                        "enriched_context": thread.enriched_context.model_dump()
                        if thread.enriched_context
                        else None,
                    }

                    if thread.is_resolved and existing.get("local_status") != "resolved":
                        update_data["local_status"] = "resolved"
                        update_data["resolution_type"] = "manual_on_github"
                        logger.info(f"Thread {thread.id} 已在 GitHub 上手动解决，同步本地状态")

                    thread_table.update(update_data, self.Thread.id == thread.id)
                else:
                    thread_table.insert(thread.model_dump())

        logger.info(f"保存了 {len(threads)} 个线程状态")

    def save_overviews(self, overviews: list[ReviewOverview], metadata: ReviewMetadata) -> None:
        """
        保存总览意见

        Args:
            overviews: 总览意见列表
            metadata: 元数据
        """
        with FileLock(self.lock_path):
            overview_table = self.db.table("overviews")

            for overview in overviews:
                existing = overview_table.get(self.Overview.id == overview.id)

                if existing:
                    overview_table.update(overview.model_dump(), self.Overview.id == overview.id)
                else:
                    overview_table.insert(overview.model_dump())

        logger.info(f"保存了 {len(overviews)} 个总览意见")

    def mark_resolved_locally(self, thread_id: str, resolution_type: str) -> None:
        """
        API 调用成功后，更新本地状态

        Args:
            thread_id: Thread ID
            resolution_type: 解决依据类型
        """
        with FileLock(self.lock_path):
            self.db.table("threads").update(
                {
                    "local_status": "resolved",
                    "is_resolved": True,
                    "resolution_type": resolution_type,
                    "last_updated": datetime.utcnow().isoformat(),
                },
                self.Thread.id == thread_id,
            )

        logger.info(f"Thread {thread_id} 本地状态已更新为 resolved ({resolution_type})")

    def get_all_threads(self) -> list[ReviewThreadState]:
        """获取所有线程

        Returns:
            所有线程列表
        """
        with FileLock(self.lock_path):
            threads = self.db.table("threads").all()
            return [ReviewThreadState(**t) for t in threads]

    def get_thread_by_id(self, thread_id: str) -> ReviewThreadState | None:
        """
        根据 ID 获取线程

        Args:
            thread_id: Thread ID

        Returns:
            线程状态，如果不存在返回 None
        """
        with FileLock(self.lock_path):
            data = self.db.table("threads").get(self.Thread.id == thread_id)
            if data:
                return ReviewThreadState(**data)
            return None

    def get_metadata(self) -> ReviewMetadata | None:
        """
        获取元数据

        Returns:
            元数据，如果不存在返回 None
        """
        with FileLock(self.lock_path):
            meta = self.db.table("metadata").all()
            if meta:
                return ReviewMetadata(**meta[0])
            return None

    def get_all_overviews(self) -> list[ReviewOverview]:
        """
        获取所有总览意见

        Returns:
            总览意见列表
        """
        with FileLock(self.lock_path):
            overviews = self.db.table("overviews").all()
            return [ReviewOverview(**o) for o in overviews]

    def save_issue_comment_overviews(
        self, issue_comment_overviews: list[IssueCommentOverview], metadata: ReviewMetadata
    ) -> None:
        """
        保存 Issue Comment 级别的总览意见

        Args:
            issue_comment_overviews: Issue Comment 总览意见列表
            metadata: 元数据
        """
        with FileLock(self.lock_path):
            issue_comment_table = self.db.table("issue_comment_overviews")

            for overview in issue_comment_overviews:
                existing = issue_comment_table.get(Query().id == overview.id)

                if existing:
                    issue_comment_table.update(overview.model_dump(), Query().id == overview.id)
                else:
                    issue_comment_table.insert(overview.model_dump())

        logger.info(f"保存了 {len(issue_comment_overviews)} 个 Issue Comment 总览意见")

    def get_all_issue_comment_overviews(self) -> list[IssueCommentOverview]:
        """
        获取所有 Issue Comment 级别的总览意见

        Returns:
            Issue Comment 总览意见列表
        """
        with FileLock(self.lock_path):
            overviews = self.db.table("issue_comment_overviews").all()
            return [IssueCommentOverview(**o) for o in overviews]

    def acknowledge_overview(self, overview_id: str) -> bool:
        """
        确认单个总览意见

        Args:
            overview_id: 总览意见 ID

        Returns:
            是否成功
        """
        with FileLock(self.lock_path):
            overview_table = self.db.table("overviews")
            existing = overview_table.get(self.Overview.id == overview_id)

            if existing:
                overview_table.update(
                    {
                        "local_status": "acknowledged",
                        "last_updated": datetime.utcnow().isoformat(),
                    },
                    self.Overview.id == overview_id,
                )
                logger.info(f"Overview {overview_id} 已确认")
                return True
            return False

    def acknowledge_all_overviews(self) -> list[str]:
        """
        确认所有总览意见

        Returns:
            已确认的总览意见 ID 列表
        """
        with FileLock(self.lock_path):
            overview_table = self.db.table("overviews")
            overviews = overview_table.all()

            acknowledged_ids = []
            for overview in overviews:
                if overview.get("local_status") != "acknowledged":
                    overview_table.update(
                        {
                            "local_status": "acknowledged",
                            "last_updated": datetime.utcnow().isoformat(),
                        },
                        self.Overview.id == overview["id"],
                    )
                    acknowledged_ids.append(overview["id"])

            logger.info(f"已确认 {len(acknowledged_ids)} 个总览意见")
            return acknowledged_ids

    def get_statistics(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        threads = self.get_all_threads()
        overviews = self.get_all_overviews()
        issue_comment_overviews = self.get_all_issue_comment_overviews()

        total = len(threads)
        by_status = {}
        by_source = {}

        for thread in threads:
            status = thread.local_status
            source = thread.source

            by_status[status] = by_status.get(status, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
            "by_source": by_source,
            "overviews_count": len(overviews),
            "issue_comment_overviews_count": len(issue_comment_overviews),
        }
