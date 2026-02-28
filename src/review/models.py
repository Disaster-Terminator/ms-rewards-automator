from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EnrichedContext(BaseModel):
    """
    从摘要或评论正文中提取的结构化元数据

    用于将 Sourcery Prompt 或 Qodo Emoji 类型信息注入到 ReviewThreadState
    """

    issue_type: str = Field(
        default="suggestion", description="问题类型（原始值），可能包含多个类型如 'Bug, Security'"
    )
    issue_to_address: str | None = Field(None, description="问题描述（来自 Sourcery Prompt）")
    code_context: str | None = Field(None, description="代码上下文（来自 Sourcery Prompt）")


class IndividualCommentSchema(BaseModel):
    """Prompt for AI Agents 中的单个评论（用于序列化）"""

    location: str = Field(default="", description="位置字符串，如 'pyproject.toml:35'")
    file_path: str = Field(default="", description="文件路径")
    line_number: int = Field(default=0, description="行号")
    code_context: str = Field(default="", description="代码上下文")
    issue_to_address: str = Field(default="", description="问题描述")


class ReviewThreadState(BaseModel):
    """
    审查线程模型 (对应 GitHub ReviewThread)
    注意：我们解决的是 Thread，而不是单个 Comment
    """

    id: str = Field(..., description="GraphQL Node ID (Base64), 用于 mutation")
    is_resolved: bool = Field(False, description="GitHub 上的解决状态")

    primary_comment_body: str = Field(default="", description="线程中的第一条评论内容")
    comment_url: str = Field(default="", description="评论 URL")

    source: str = Field(..., description="评论来源：Sourcery/Qodo/Copilot")
    file_path: str = Field(default="", description="文件路径")
    line_number: int | None = Field(default=None, description="行号，None 表示文件级评论")

    local_status: str = Field("pending", description="本地处理状态：pending/resolved/ignored")
    resolution_type: str | None = Field(
        None,
        description="解决依据类型：code_fixed/adopted/rejected/false_positive/outdated/manual_on_github",
    )

    enriched_context: EnrichedContext | None = Field(None, description="从摘要映射的结构化元数据")

    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReviewOverview(BaseModel):
    """
    Review 级别的总览意见模型

    Sourcery 的总览意见特点：
    - 无法单独解决（没有 Thread ID）
    - 包含 "high level feedback"
    - 包含 "Prompt for AI Agents"（结构化摘要）
    """

    id: str = Field(..., description="Review ID")
    body: str = Field(default="", description="Review 完整内容")
    source: str = Field(..., description="评论来源：Sourcery/Qodo/Copilot")
    url: str = Field(default="", description="Review URL")
    state: str = Field(default="COMMENTED", description="Review 状态")
    submitted_at: str | None = Field(None, description="提交时间")

    high_level_feedback: list[str] = Field(default_factory=list, description="提取的高层次反馈列表")
    has_prompt_for_ai: bool = Field(False, description="是否包含 AI Agent Prompt")

    prompt_overall_comments: list[str] = Field(
        default_factory=list, description="Prompt for AI Agents 中的 Overall Comments"
    )
    prompt_individual_comments: list[IndividualCommentSchema] = Field(
        default_factory=list, description="Prompt for AI Agents 中的 Individual Comments（结构化）"
    )

    is_code_change_summary: bool = Field(
        False,
        description="是否为代码变化摘要（非改进意见）：Sourcery Reviewer's Guide / Qodo Review Summary",
    )

    local_status: Literal["pending", "acknowledged"] = Field(
        "pending", description="本地处理状态：pending/acknowledged（总览意见只能确认，无法解决）"
    )

    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IssueCommentOverview(BaseModel):
    """
    Issue Comment 级别的总览意见模型

    注意：这是只读参考文档，不需要状态追踪。
    Qodo v2 的所有问题都通过 Review Thread 获取，Issue Comment 仅作为参考。
    """

    id: str = Field(..., description="Issue Comment ID")
    body: str = Field(default="", description="Comment 完整内容")
    source: str = Field(default="Qodo", description="评论来源")
    url: str = Field(default="", description="Comment URL")
    created_at: str | None = Field(None, description="创建时间")
    user_login: str = Field(default="", description="评论者用户名")

    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReviewMetadata(BaseModel):
    """元数据模型"""

    pr_number: int
    owner: str
    repo: str
    branch: str = Field(default="", description="拉取评论时的分支名称")
    head_sha: str = Field(default="", description="拉取评论时的 HEAD commit SHA（前7位）")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "2.3"
    etag_comments: str | None = Field(None, description="GitHub ETag，用于条件请求")
    etag_reviews: str | None = Field(None, description="Reviews ETag")


class ReviewDbSchema(BaseModel):
    """数据库 Schema"""

    metadata: ReviewMetadata
    threads: list[ReviewThreadState] = Field(default_factory=list)
    overviews: list[ReviewOverview] = Field(default_factory=list)
    issue_comment_overviews: list[IssueCommentOverview] = Field(default_factory=list)
