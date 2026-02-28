import logging
import subprocess

from .comment_manager import ReviewManager
from .graphql_client import GraphQLClient
from .models import (
    EnrichedContext,
    IndividualCommentSchema,
    IssueCommentOverview,
    ReviewMetadata,
    ReviewOverview,
    ReviewThreadState,
)
from .parsers import ReviewParser

logger = logging.getLogger(__name__)


def get_git_branch() -> str:
    """获取当前 git 分支名称"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def get_git_head_sha() -> str:
    """获取当前 HEAD commit SHA（前7位）"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


class ReviewResolver:
    """
    评论解决器 - 整合所有组件
    遵循 "API First, DB Second" 原则
    """

    def __init__(
        self, token: str, owner: str, repo: str, db_path: str = ".trae/data/review_threads.json"
    ):
        self.token = token
        self.owner = owner
        self.repo = repo

        self.graphql_client = GraphQLClient(token)
        self.manager = ReviewManager(db_path)

    def fetch_threads(self, pr_number: int) -> dict:
        """
        获取 PR 的所有评论（线程 + 总览意见 + Issue Comments）

        Args:
            pr_number: PR 编号

        Returns:
            操作结果
        """
        logger.info(f"获取 PR #{pr_number} 的评论...")

        try:
            raw_threads = self.graphql_client.fetch_pr_threads(self.owner, self.repo, pr_number)

            threads = []
            for raw in raw_threads:
                comments = raw.get("comments", {}).get("nodes", [])
                first_comment = comments[0] if comments else {}

                author_login = first_comment.get("author", {}).get("login", "")
                source = ReviewParser.detect_source(author_login)

                thread = ReviewThreadState(
                    id=raw["id"],
                    is_resolved=raw.get("isResolved", False),
                    primary_comment_body=first_comment.get("body", ""),
                    comment_url=first_comment.get("url", ""),
                    source=source,
                    file_path=raw.get("path") or "",
                    line_number=raw.get("line"),
                    local_status=ReviewParser.parse_status(
                        first_comment.get("body", ""), raw.get("isResolved", False)
                    ),
                )
                threads.append(thread)

            raw_reviews = self.graphql_client.fetch_pr_reviews(self.owner, self.repo, pr_number)

            overviews = []
            prompt_individual_comments = []

            for raw in raw_reviews:
                author_login = raw.get("author", {}).get("login", "")
                source = ReviewParser.detect_source(author_login)
                body = raw.get("body", "")

                if ReviewParser.is_overview_review(body, source):
                    high_level_feedback, has_prompt_for_ai = ReviewParser.parse_sourcery_overview(
                        body
                    )

                    prompt_for_ai = ReviewParser.parse_prompt_for_ai(body)
                    prompt_overall_comments = []
                    prompt_individual_comment_schemas = []

                    if prompt_for_ai:
                        prompt_overall_comments = prompt_for_ai.overall_comments
                        for c in prompt_for_ai.individual_comments:
                            prompt_individual_comments.append(
                                {
                                    "file_path": c.file_path,
                                    "line_number": c.line_number,
                                    "issue_to_address": c.issue_to_address,
                                    "code_context": c.code_context,
                                }
                            )
                            line_num = c.line_number if isinstance(c.line_number, int) else 0
                            prompt_individual_comment_schemas.append(
                                IndividualCommentSchema(
                                    location=c.location,
                                    file_path=c.file_path,
                                    line_number=line_num,
                                    code_context=c.code_context,
                                    issue_to_address=c.issue_to_address,
                                )
                            )

                    overview = ReviewOverview(
                        id=raw["id"],
                        body=body,
                        source=source,
                        url=raw.get("url", ""),
                        state=raw.get("state", "COMMENTED"),
                        submitted_at=raw.get("submittedAt"),
                        high_level_feedback=high_level_feedback,
                        has_prompt_for_ai=has_prompt_for_ai,
                        prompt_overall_comments=prompt_overall_comments,
                        prompt_individual_comments=prompt_individual_comment_schemas,
                    )
                    overviews.append(overview)

            raw_issue_comments = self.graphql_client.fetch_issue_comments(
                self.owner, self.repo, pr_number
            )

            issue_comment_overviews = []
            for raw in raw_issue_comments:
                author_login = raw.get("user", {}).get("login", "")
                body = raw.get("body", "")

                if "qodo" in author_login.lower() or "codium" in author_login.lower():
                    issue_comment_overviews.append(
                        IssueCommentOverview(
                            id=str(raw.get("id", "")),
                            body=body,
                            source="Qodo",
                            url=raw.get("html_url", ""),
                            created_at=raw.get("created_at"),
                            user_login=author_login,
                        )
                    )

            threads = self._map_prompt_to_threads(threads, prompt_individual_comments)

            threads = self._inject_qodo_types(threads)

            threads = self._inject_sourcery_types(threads)

            branch = get_git_branch()
            head_sha = get_git_head_sha()

            metadata = ReviewMetadata(
                pr_number=pr_number,
                owner=self.owner,
                repo=self.repo,
                branch=branch,
                head_sha=head_sha,
            )

            self.manager.save_threads(threads, metadata)
            self.manager.save_overviews(overviews, metadata)
            self.manager.save_issue_comment_overviews(issue_comment_overviews, metadata)

            stats = self.manager.get_statistics()

            return {
                "success": True,
                "message": f"获取了 {len(threads)} 个线程, {len(overviews)} 个总览意见, {len(issue_comment_overviews)} 个 Issue Comments",
                "threads_count": len(threads),
                "overviews_count": len(overviews),
                "issue_comments_count": len(issue_comment_overviews),
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"获取评论失败: {e}")
            return {"success": False, "message": "获取评论失败，请查看日志了解详情"}

    def _map_prompt_to_threads(
        self, threads: list[ReviewThreadState], prompt_comments: list[dict]
    ) -> list[ReviewThreadState]:
        """
        将 Sourcery Prompt Individual Comments 映射到 Thread

        使用 Left Join 策略：
        - 只保留能匹配到活跃 Thread 的摘要
        - 找不到匹配 Thread 时丢弃摘要

        支持行号范围匹配：
        - 精确匹配：`pyproject.toml:35` 匹配 line=35
        - 范围匹配：`src/file.py:10-20` 匹配 line 在 10-20 范围内的 Thread
        - 文件级匹配：`line=None` 时按文件路径匹配

        Args:
            threads: Thread 列表
            prompt_comments: Prompt Individual Comments 列表

        Returns:
            注入了 enriched_context 的 Thread 列表
        """
        if not prompt_comments:
            return threads

        exact_index = {}
        file_index = {}

        for thread in threads:
            if not thread.is_resolved:
                if thread.line_number is not None and thread.line_number > 0:
                    key = (thread.file_path, thread.line_number)
                    exact_index[key] = thread
                else:
                    if thread.file_path not in file_index:
                        file_index[thread.file_path] = []
                    file_index[thread.file_path].append(thread)

        for comment in prompt_comments:
            file_path = comment.get("file_path", "")
            line_info = comment.get("line_number", 0)

            if not file_path:
                continue

            matching_thread = None

            if isinstance(line_info, tuple):
                line_start, line_end = line_info
                for line in range(line_start, line_end + 1):
                    key = (file_path, line)
                    if key in exact_index:
                        matching_thread = exact_index[key]
                        break
            elif line_info is None or line_info == 0:
                if file_path in file_index:
                    matching_thread = file_index[file_path][0]
            else:
                key = (file_path, line_info)
                matching_thread = exact_index.get(key)

            if matching_thread and not matching_thread.enriched_context:
                matching_thread.enriched_context = EnrichedContext(
                    issue_type="suggestion",
                    issue_to_address=comment.get("issue_to_address"),
                    code_context=comment.get("code_context"),
                )
                logger.debug(f"映射 Prompt 到 Thread: {file_path}:{line_info}")

        return threads

    def _inject_qodo_types(self, threads: list[ReviewThreadState]) -> list[ReviewThreadState]:
        """
        为 Qodo Thread 注入类型信息和 Agent Prompt 内容

        Args:
            threads: Thread 列表

        Returns:
            注入了类型信息和 Agent Prompt 内容的 Thread 列表
        """
        for thread in threads:
            if thread.source == "Qodo" and not thread.enriched_context:
                issue_type = ReviewParser.parse_qodo_issue_types(thread.primary_comment_body)

                agent_prompt = ReviewParser.parse_qodo_agent_prompt(thread.primary_comment_body)

                thread.enriched_context = EnrichedContext(
                    issue_type=issue_type,
                    issue_to_address=agent_prompt.get("issue_description"),
                    code_context=agent_prompt.get("fix_focus_areas"),
                )
                logger.debug(f"注入 Qodo 类型到 Thread: {issue_type}")

        return threads

    def _inject_sourcery_types(self, threads: list[ReviewThreadState]) -> list[ReviewThreadState]:
        """
        为 Sourcery Thread 注入类型信息（从 primary_comment_body 解析）

        Args:
            threads: Thread 列表

        Returns:
            注入了类型信息的 Thread 列表
        """
        for thread in threads:
            if thread.source == "Sourcery" and not thread.enriched_context:
                parsed = ReviewParser.parse_sourcery_thread_body(thread.primary_comment_body)
                if parsed.get("issue_type"):
                    thread.enriched_context = EnrichedContext(
                        issue_type=parsed["issue_type"],
                        issue_to_address=parsed.get("issue_to_address"),
                    )
                    logger.debug(f"注入 Sourcery 类型到 Thread: {parsed['issue_type']}")

        return threads

    def resolve_thread(
        self, thread_id: str, resolution_type: str, reply_text: str | None = None
    ) -> dict:
        """
        执行解决流程：回复(可选) -> 解决(API) -> 更新本地DB

        遵循 "API First, DB Second" 原则：
        1. 先调用 GitHub API
        2. 只有 API 成功后才更新本地数据库

        Args:
            thread_id: Thread ID
            resolution_type: 解决依据类型
            reply_text: 可选的回复内容

        Returns:
            操作结果
        """
        logger.info(f"解决线程 {thread_id}, 类型: {resolution_type}")

        thread = self.manager.get_thread_by_id(thread_id)
        if not thread:
            return {"success": False, "message": f"线程 {thread_id} 不存在"}

        if thread.is_resolved:
            return {
                "success": True,
                "message": f"线程 {thread_id} 已在 GitHub 上解决",
                "already_resolved": True,
            }

        if reply_text:
            try:
                self.graphql_client.reply_to_thread(thread_id, reply_text)
            except Exception as e:
                logger.error(f"回复失败: {e}")
                return {"success": False, "message": "回复失败，请查看日志了解详情"}

        try:
            is_resolved_remote = self.graphql_client.resolve_thread(thread_id)

            if not is_resolved_remote:
                return {"success": False, "message": "GitHub API 返回解决失败"}

        except Exception as e:
            logger.error(f"API 解决失败: {e}")
            return {"success": False, "message": "API 解决失败，请查看日志了解详情"}

        self.manager.mark_resolved_locally(thread_id, resolution_type)

        return {
            "success": True,
            "message": f"线程 {thread_id} 已解决",
            "resolution_type": resolution_type,
            "reply_posted": reply_text is not None,
        }

    def get_pending_threads(self) -> list[ReviewThreadState]:
        """
        获取所有待处理的线程

        Returns:
            待处理线程列表
        """
        return self.manager.get_pending_threads()

    def get_statistics(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.manager.get_statistics()

    def list_threads(
        self, status: str | None = None, source: str | None = None
    ) -> list[ReviewThreadState]:
        """
        列出线程（支持过滤）

        Args:
            status: 按状态过滤（pending/resolved/ignored）
            source: 按来源过滤（Sourcery/Qodo/Copilot）

        Returns:
            过滤后的线程列表
        """
        threads = self.manager.get_all_threads()

        if status:
            threads = [t for t in threads if t.local_status == status]

        if source:
            threads = [t for t in threads if t.source == source]

        return threads
