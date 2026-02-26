import logging
import time
from typing import Any

import httpx

from constants import GITHUB_URLS

logger = logging.getLogger(__name__)


class GraphQLClient:
    """GitHub GraphQL 客户端 - 获取完整评论（避免截断）"""

    def __init__(self, token: str, max_retries: int = 3, base_delay: float = 1.0):
        self.token = token
        self.endpoint = GITHUB_URLS["graphql"]
        self.rest_endpoint = GITHUB_URLS["rest"]
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _execute_with_retry(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        执行 GraphQL 查询（带重试机制）

        Args:
            query: GraphQL 查询语句
            variables: 查询变量

        Returns:
            查询结果数据

        Raises:
            Exception: GraphQL 错误或网络错误
        """
        if variables is None:
            variables = {}

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = httpx.post(
                    self.endpoint,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=30.0,
                )

                response.raise_for_status()

                data = response.json()

                if "errors" in data:
                    error_msg = (
                        data["errors"][0].get("message", "未知错误")
                        if data["errors"]
                        else "未知错误"
                    )

                    if "rate limit" in error_msg.lower():
                        if attempt < self.max_retries - 1:
                            wait_time = self.base_delay * (2**attempt) * 2
                            logger.warning(
                                f"触发速率限制，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                        raise Exception(f"GitHub API 速率限制: {error_msg}")

                    raise Exception(f"GraphQL 错误: {error_msg}")

                return data["data"]

            except httpx.TimeoutException:
                last_exception = Exception("网络请求超时，请检查网络连接后重试")
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 502, 503, 504]:
                    if attempt < self.max_retries - 1:
                        wait_time = self.base_delay * (2**attempt)
                        logger.warning(
                            f"HTTP {e.response.status_code}，等待 {wait_time}s 后重试 (尝试 {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                last_exception = Exception(
                    f"API 请求失败 (HTTP {e.response.status_code})，请稍后重试"
                )
            except httpx.RequestError as e:
                last_exception = Exception(f"网络连接失败: {str(e)}")
                logger.warning(f"网络错误: {e} (尝试 {attempt + 1}/{self.max_retries})")
            except Exception as e:
                if "GraphQL 错误" in str(e) or "速率限制" in str(e):
                    raise
                last_exception = e

            if attempt < self.max_retries - 1:
                wait_time = self.base_delay * (2**attempt)
                logger.info(f"等待 {wait_time}s 后重试...")
                time.sleep(wait_time)

        logger.error(f"重试 {self.max_retries} 次后仍然失败")
        raise last_exception

    def _execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        执行 GraphQL 查询

        Args:
            query: GraphQL 查询语句
            variables: 查询变量

        Returns:
            查询结果数据

        Raises:
            Exception: GraphQL 错误或网络错误
        """
        return self._execute_with_retry(query, variables)

    def fetch_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """
        获取 PR 的评论线程 (包含 Thread ID) - 支持分页

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            pr_number: PR 编号

        Returns:
            线程列表，每个线程包含 id (Thread ID)、isResolved、path、line 等
        """
        all_threads = []
        has_next_page = True
        cursor = None
        page_count = 0

        while has_next_page:
            page_count += 1

            if cursor:
                query = """
                query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
                  repository(owner: $owner, name: $repo) {
                    pullRequest(number: $pr) {
                      reviewThreads(first: 50, after: $cursor) {
                        pageInfo {
                          hasNextPage
                          endCursor
                        }
                        nodes {
                          id
                          isResolved
                          path
                          line
                          comments(first: 1) {
                            nodes {
                              author { login }
                              body
                              url
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """
                variables = {"owner": owner, "repo": repo, "pr": pr_number, "cursor": cursor}
            else:
                query = """
                query($owner: String!, $repo: String!, $pr: Int!) {
                  repository(owner: $owner, name: $repo) {
                    pullRequest(number: $pr) {
                      reviewThreads(first: 50) {
                        pageInfo {
                          hasNextPage
                          endCursor
                        }
                        nodes {
                          id
                          isResolved
                          path
                          line
                          comments(first: 1) {
                            nodes {
                              author { login }
                              body
                              url
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """
                variables = {"owner": owner, "repo": repo, "pr": pr_number}

            data = self._execute(query, variables)

            thread_data = data["repository"]["pullRequest"]["reviewThreads"]
            threads = thread_data["nodes"]
            all_threads.extend(threads)

            page_info = thread_data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            logger.debug(
                f"获取第 {page_count} 页，{len(threads)} 条线程，总计 {len(all_threads)} 条"
            )

            if not has_next_page:
                break

        logger.info(f"共获取 {len(all_threads)} 条评论线程 ({page_count} 页)")
        return all_threads

    def fetch_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """
        获取 PR 的 Review 级别评论（总览意见）

        Sourcery 的总览意见在 reviews API 中，包含：
        - "high level feedback"（无法单独解决）
        - "Prompt for AI Agents"

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            pr_number: PR 编号

        Returns:
            Review 列表，每个包含 id、body、author 等
        """
        query = """
        query($owner: String!, $repo: String!, $pr: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $pr) {
              reviews(last: 20) {
                nodes {
                  id
                  body
                  state
                  author { login }
                  url
                  submittedAt
                }
              }
            }
          }
        }
        """

        data = self._execute(query, {"owner": owner, "repo": repo, "pr": pr_number})

        reviews = data["repository"]["pullRequest"]["reviews"]["nodes"]

        return reviews

    def resolve_thread(self, thread_id: str) -> bool:
        """
        解决线程 (Mutation)

        Args:
            thread_id: Thread 的 GraphQL Node ID

        Returns:
            True 如果解决成功

        Raises:
            Exception: API 调用失败
        """
        mutation = """
        mutation($threadId: ID!) {
          resolveReviewThread(input: {threadId: $threadId}) {
            thread {
              isResolved
            }
          }
        }
        """

        try:
            data = self._execute(mutation, {"threadId": thread_id})
            is_resolved = data["resolveReviewThread"]["thread"]["isResolved"]
            logger.info(f"Thread {thread_id} resolved: {is_resolved}")
            return is_resolved
        except Exception as e:
            logger.error(f"Failed to resolve thread {thread_id}: {e}")
            raise

    def reply_to_thread(self, thread_id: str, body: str) -> str:
        """
        在线程下回复 (Mutation)

        Args:
            thread_id: Thread 的 GraphQL Node ID
            body: 回复内容

        Returns:
            新评论的 ID

        Raises:
            Exception: API 调用失败
        """
        mutation = """
        mutation($threadId: ID!, $body: String!) {
          addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
            comment {
              id
            }
          }
        }
        """

        try:
            data = self._execute(mutation, {"threadId": thread_id, "body": body})
            comment_id = data["addPullRequestReviewThreadReply"]["comment"]["id"]
            logger.info(f"Reply posted to thread {thread_id}, comment ID: {comment_id}")
            return comment_id
        except Exception as e:
            logger.error(f"Failed to reply to thread {thread_id}: {e}")
            raise

    def fetch_issue_comments(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """
        获取 PR 的 Issue Comments（REST API）

        Qodo 的 Code Review 信息存储在 Issue Comments 中。
        Issue Comments 是 PR 页面上的普通评论。

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            pr_number: PR 编号

        Returns:
            Issue Comment 列表，每个包含 id、body、user、created_at 等
        """
        url = f"{self.rest_endpoint}/repos/{owner}/{repo}/issues/{pr_number}/comments"

        all_comments = []
        page = 1

        while True:
            response = httpx.get(
                url, headers=self.headers, params={"page": page, "per_page": 100}, timeout=30.0
            )

            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            all_comments.extend(comments)
            page += 1

            if len(comments) < 100:
                break

        logger.info(f"Fetched {len(all_comments)} issue comments for PR #{pr_number}")
        return all_comments
