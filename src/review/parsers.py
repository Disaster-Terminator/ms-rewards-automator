import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class IndividualComment:
    """Prompt for AI Agents 中的单个评论"""

    location: str
    file_path: str
    line_number: int
    code_context: str
    issue_to_address: str


@dataclass
class PromptForAI:
    """解析后的 Prompt for AI Agents 结构"""

    overall_comments: list[str]
    individual_comments: list[IndividualComment]


@dataclass
class PRReviewerGuide:
    """解析后的 Qodo PR Reviewer Guide 结构"""

    commit_hash: str
    estimated_effort: str
    has_tests: bool
    security_concerns: str | None
    focus_areas: list[str]
    issues: list[tuple[str, str]]


class ReviewParser:
    """
    AI 审查评论解析器
    用于解析 Qodo/Sourcery/Copilot 的评论状态
    """

    REGEX_RESOLVED = re.compile(
        r"^\s*(?:[-*]\s*)?(?:☑|✅\s*Addressed)", re.MULTILINE | re.IGNORECASE
    )

    REGEX_CATEGORY = re.compile(r"^\s*✓\s+\w+", re.MULTILINE)

    REGEX_HIGH_LEVEL_FEEDBACK = re.compile(
        r"(?:high level feedback|overall comments?):?\s*\n([\s\S]*?)(?=\n<details>|\n\*\*\*|\n---|\Z)",
        re.IGNORECASE,
    )

    REGEX_LIST_ITEM = re.compile(r"^\s*-\s+(.+)$", re.MULTILINE)

    REGEX_PROMPT_FOR_AI = re.compile(
        r"<details>\s*<summary>\s*Prompt for AI Agents\s*</summary>\s*~~~markdown\s*([\s\S]*?)\s*~~~\s*</details>",
        re.IGNORECASE,
    )

    REGEX_LOCATION = re.compile(
        r"<location>\s*`?([^`:\s]+(?::\d+(?:-\d+)?)?)`?\s*</location>", re.IGNORECASE
    )

    REGEX_CODE_CONTEXT = re.compile(r"<code_context>\s*([\s\S]*?)\s*</code_context>", re.IGNORECASE)

    REGEX_ISSUE_TO_ADDRESS = re.compile(
        r"<issue_to_address>\s*([\s\S]*?)\s*</issue_to_address>", re.IGNORECASE
    )

    REGEX_INDIVIDUAL_COMMENT = re.compile(
        r"### Comment \d+\s*\n([\s\S]*?)(?=### Comment \d+|\Z)", re.IGNORECASE
    )

    @classmethod
    def parse_status(cls, body: str, is_resolved_on_github: bool) -> Literal["resolved", "pending"]:
        """
        解析评论状态
        优先级：GitHub原生状态 > AI文本标记 > 默认

        Args:
            body: 评论内容
            is_resolved_on_github: GitHub 上的解决状态

        Returns:
            "resolved" 或 "pending"
        """
        if is_resolved_on_github:
            return "resolved"

        body = body.strip() if body else ""

        if cls.REGEX_RESOLVED.search(body):
            return "resolved"

        if cls.REGEX_CATEGORY.match(body):
            return "pending"

        return "pending"

    @classmethod
    def is_auto_resolved(cls, body: str) -> bool:
        """
        检测评论是否已被 AI 工具自动标记为已解决

        Args:
            body: 评论内容

        Returns:
            True 如果检测到解决标志
        """
        if not body:
            return False
        return bool(cls.REGEX_RESOLVED.search(body))

    @classmethod
    def detect_source(cls, author_login: str) -> Literal["Sourcery", "Qodo", "Copilot", "Unknown"]:
        """
        检测评论来源

        Args:
            author_login: 评论作者的 GitHub 用户名

        Returns:
            评论来源标识
        """
        login = author_login.lower() if author_login else ""

        if "sourcery" in login:
            return "Sourcery"
        elif "qodo" in login or "codium" in login:
            return "Qodo"
        elif "copilot" in login:
            return "Copilot"

        return "Unknown"

    @classmethod
    def parse_sourcery_overview(cls, body: str) -> tuple[list[str], bool]:
        """
        解析 Sourcery 总览意见

        提取：
        1. high level feedback 列表
        2. 是否包含 "Prompt for AI Agents"

        Args:
            body: Review 的完整内容

        Returns:
            (high_level_feedback_list, has_prompt_for_ai)
        """
        if not body:
            return [], False

        has_prompt_for_ai = "Prompt for AI Agents" in body

        feedback_list = []

        match = cls.REGEX_HIGH_LEVEL_FEEDBACK.search(body)
        if match:
            feedback_section = match.group(1)
            list_items = cls.REGEX_LIST_ITEM.findall(feedback_section)
            feedback_list = [item.strip() for item in list_items if item.strip()]

        if not feedback_list:
            lines = body.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("- ") and not line.startswith("- ["):
                    content = line[2:].strip()
                    if content and len(content) > 20:
                        feedback_list.append(content)

        return feedback_list, has_prompt_for_ai

    @classmethod
    def is_overview_review(cls, body: str, source: str) -> bool:
        """
        判断是否为总览意见（非行内评论）

        Args:
            body: Review 内容
            source: 评论来源

        Returns:
            True 如果是总览意见
        """
        if not body:
            return False

        if source == "Sourcery":
            return "high level feedback" in body.lower() or "Prompt for AI Agents" in body

        if source == "Copilot":
            return "Pull request overview" in body or "Reviewed changes" in body

        return False

    @classmethod
    def parse_prompt_for_ai(cls, body: str) -> PromptForAI | None:
        """
        解析 Prompt for AI Agents 结构化内容

        这是 Sourcery 提供的完整审查摘要，包含：
        - Overall Comments（总览意见）
        - Individual Comments（具体 issue，带位置信息）

        Args:
            body: Review 的完整内容

        Returns:
            PromptForAI 对象，如果不存在返回 None
        """
        if not body or "Prompt for AI Agents" not in body:
            return None

        match = cls.REGEX_PROMPT_FOR_AI.search(body)
        if not match:
            return None

        prompt_content = match.group(1)

        overall_comments = []
        overall_match = re.search(
            r"## Overall Comments\s*\n([\s\S]*?)(?=\n## |\Z)", prompt_content, re.IGNORECASE
        )
        if overall_match:
            overall_section = overall_match.group(1)
            overall_comments = cls.REGEX_LIST_ITEM.findall(overall_section)
            overall_comments = [c.strip() for c in overall_comments if c.strip()]

        individual_comments = []
        for comment_match in cls.REGEX_INDIVIDUAL_COMMENT.finditer(prompt_content):
            comment_block = comment_match.group(1)

            location_match = cls.REGEX_LOCATION.search(comment_block)
            code_match = cls.REGEX_CODE_CONTEXT.search(comment_block)
            issue_match = cls.REGEX_ISSUE_TO_ADDRESS.search(comment_block)

            if location_match and issue_match:
                location = location_match.group(1).strip()
                file_path, line_number = cls._parse_location(location)

                individual_comments.append(
                    IndividualComment(
                        location=location,
                        file_path=file_path,
                        line_number=line_number,
                        code_context=code_match.group(1).strip() if code_match else "",
                        issue_to_address=issue_match.group(1).strip(),
                    )
                )

        return PromptForAI(
            overall_comments=overall_comments, individual_comments=individual_comments
        )

    @classmethod
    def _parse_location(cls, location: str) -> tuple[str, int]:
        """
        解析位置字符串，提取文件路径和行号

        Args:
            location: 位置字符串，如 "pyproject.toml:35" 或 "src/file.py:10-20"

        Returns:
            (file_path, line_number)
        """
        if ":" in location:
            parts = location.split(":")
            file_path = parts[0].strip()
            try:
                line_number = int(parts[1].split("-")[0].strip())
            except (ValueError, IndexError):
                line_number = 0
        else:
            file_path = location.strip()
            line_number = 0

        return file_path, line_number

    REGEX_PR_REVIEWER_GUIDE = re.compile(r"PR Reviewer Guide 🔍", re.IGNORECASE)

    REGEX_COMMIT_HASH = re.compile(r"Review updated until commit ([a-f0-9]+)", re.IGNORECASE)

    REGEX_ESTIMATED_EFFORT = re.compile(r"⏱️ Estimated effort to review:\s*(.+)", re.IGNORECASE)

    REGEX_HAS_TESTS = re.compile(r"🧪 PR contains tests", re.IGNORECASE)

    REGEX_SECURITY = re.compile(r"🔒\s*(.+?security.+)", re.IGNORECASE)

    REGEX_FOCUS_AREAS = re.compile(
        r"⚡ Recommended focus areas for review\s*\n([\s\S]*?)(?=\n\n|\n[🐞📘⛨⚯]|\Z)", re.IGNORECASE
    )

    REGEX_ISSUE_SECTION = re.compile(r"([🐞📘⛨⚯]\s*\w+[^✓]*)", re.MULTILINE)

    @classmethod
    def parse_pr_reviewer_guide(cls, body: str) -> PRReviewerGuide | None:
        """
        解析 Qodo PR Reviewer Guide

        这是 Qodo 提供的审查指南，包含：
        - 审查工作量估算
        - 安全问题摘要
        - 重点审查区域
        - 改进意见摘要

        Args:
            body: Issue Comment 的完整内容

        Returns:
            PRReviewerGuide 对象，如果不是 PR Reviewer Guide 返回 None
        """
        if not body or not cls.REGEX_PR_REVIEWER_GUIDE.search(body):
            return None

        commit_hash = ""
        commit_match = cls.REGEX_COMMIT_HASH.search(body)
        if commit_match:
            commit_hash = commit_match.group(1)

        estimated_effort = ""
        effort_match = cls.REGEX_ESTIMATED_EFFORT.search(body)
        if effort_match:
            estimated_effort = effort_match.group(1).strip()

        has_tests = bool(cls.REGEX_HAS_TESTS.search(body))

        security_concerns = None
        security_match = cls.REGEX_SECURITY.search(body)
        if security_match:
            security_concerns = security_match.group(1).strip()

        focus_areas = []
        focus_match = cls.REGEX_FOCUS_AREAS.search(body)
        if focus_match:
            focus_section = focus_match.group(1)
            focus_areas = [
                line.strip().lstrip("- ").strip()
                for line in focus_section.split("\n")
                if line.strip().startswith("-")
            ]

        issues = []
        issue_matches = cls.REGEX_ISSUE_SECTION.findall(body)
        for issue_block in issue_matches:
            lines = issue_block.strip().split("\n")
            if lines:
                issue_type = lines[0].strip()
                issue_desc = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                issues.append((issue_type, issue_desc))

        return PRReviewerGuide(
            commit_hash=commit_hash,
            estimated_effort=estimated_effort,
            has_tests=has_tests,
            security_concerns=security_concerns,
            focus_areas=focus_areas,
            issues=issues,
        )

    @classmethod
    def is_qodo_review_summary(cls, body: str) -> bool:
        """
        判断是否为 Qodo Review Summary（代码变化摘要）

        注意：这是代码变化摘要，不是改进意见！

        Args:
            body: 评论内容

        Returns:
            True 如果是 Review Summary
        """
        if not body:
            return False
        return "Review Summary by Qodo" in body

    @classmethod
    def is_qodo_pr_reviewer_guide(cls, body: str) -> bool:
        """
        判断是否为 Qodo PR Reviewer Guide（改进意见摘要）

        这是 Qodo 提供的审查指南，包含改进意见摘要。

        Args:
            body: 评论内容

        Returns:
            True 如果是 PR Reviewer Guide
        """
        if not body:
            return False
        return "PR Reviewer Guide" in body

    @classmethod
    def is_sourcery_reviewer_guide(cls, body: str) -> bool:
        """
        判断是否为 Sourcery Reviewer's Guide（代码变化摘要）

        注意：这是代码变化摘要，不是改进意见！

        Args:
            body: 评论内容

        Returns:
            True 如果是 Reviewer's Guide
        """
        if not body:
            return False
        return "Reviewer's Guide" in body and "high level feedback" not in body.lower()

    REGEX_QODO_EMOJI_TYPES = re.compile(
        r"<code>\s*(?:🐞\s*)?Bug\s*</code>|"
        r"<code>\s*(?:📘\s*)?Rule\s*violation\s*</code>|"
        r"<code>\s*(?:⛨\s*)?Security\s*</code>|"
        r"<code>\s*(?:⚯\s*)?Reliability\s*</code>|"
        r"<code>\s*(?:✓\s*)?Correctness\s*</code>|"
        r"Bug|Rule\s*violation|Security|Reliability|Correctness",
        re.IGNORECASE,
    )

    QODO_TYPE_MAP = {
        "bug": "Bug",
        "rule violation": "Rule violation",
        "security": "Security",
        "reliability": "Reliability",
        "correctness": "Correctness",
    }

    @classmethod
    def parse_qodo_issue_types(cls, body: str) -> str:
        """
        解析 Qodo 评论正文中的类型信息

        支持的格式：
        - <code>📘 Rule violation</code>
        - <code>🐞 Bug</code>
        - 纯文本：Bug, Security 等

        Args:
            body: 评论正文

        Returns:
            类型字符串，多个类型用逗号拼接，如 "Bug, Security"
            如果没有匹配，返回默认值 "suggestion"
        """
        if not body:
            return "suggestion"

        matches = cls.REGEX_QODO_EMOJI_TYPES.findall(body)
        if not matches:
            return "suggestion"

        types = []
        for match in matches:
            type_str = match.lower()
            type_str = type_str.replace("<code>", "").replace("</code>", "")
            type_str = (
                type_str.replace("🐞", "")
                .replace("📘", "")
                .replace("⛨", "")
                .replace("⚯", "")
                .replace("✓", "")
            )
            type_str = type_str.strip()

            if type_str in cls.QODO_TYPE_MAP:
                resolved_type = cls.QODO_TYPE_MAP[type_str]
                if resolved_type not in types:
                    types.append(resolved_type)

        if not types:
            return "suggestion"

        return ", ".join(types)
