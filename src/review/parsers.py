import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class IndividualComment:
    """Prompt for AI Agents 中的单个评论"""

    location: str
    file_path: str
    line_number: int | tuple[int, int] | None
    code_context: str
    issue_to_address: str


@dataclass
class PromptForAI:
    """解析后的 Prompt for AI Agents 结构"""

    overall_comments: list[str]
    individual_comments: list[IndividualComment]


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
    def _parse_location(cls, location: str) -> tuple[str, int | tuple[int, int] | None]:
        """
        解析位置字符串，提取文件路径和行号

        Args:
            location: 位置字符串，如 "pyproject.toml:35" 或 "src/file.py:10-20"

        Returns:
            (file_path, line_number) 或 (file_path, (line_start, line_end)) 或 (file_path, None)
        """
        if ":" in location:
            parts = location.split(":")
            file_path = parts[0].strip()
            line_part = parts[1].strip()

            if "-" in line_part:
                try:
                    range_parts = line_part.split("-")
                    line_start = int(range_parts[0].strip())
                    line_end = int(range_parts[1].strip())
                    return file_path, (line_start, line_end)
                except (ValueError, IndexError):
                    return file_path, None
            else:
                try:
                    line_number = int(line_part)
                except ValueError:
                    line_number = None
                return file_path, line_number
        else:
            file_path = location.strip()
            return file_path, None

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

    REGEX_QODO_COMMIT_HASH = re.compile(
        r"(?:Review updated until commit|Persistent review updated to latest commit)\s+([a-f0-9]+)",
        re.IGNORECASE,
    )

    @classmethod
    def parse_qodo_commit_hash(cls, body: str) -> str | None:
        """
        解析 Qodo v2 Code Review 中的 commit hash

        Qodo v2 格式：
        - "Review updated until commit 9a074bc"
        - "Persistent review updated to latest commit 9a074bc"

        Args:
            body: Issue Comment 内容

        Returns:
            commit hash 字符串，如果不存在返回 None
        """
        if not body:
            return None
        match = cls.REGEX_QODO_COMMIT_HASH.search(body)
        if match:
            return match.group(1)
        return None

    REGEX_QODO_EMOJI_TYPES = re.compile(
        r"<code>\s*(?:🐞\s*)?Bug\s*</code>|"
        r"<code>\s*(?:📘\s*)?Rule\s*violation\s*</code>|"
        r"<code>\s*(?:⛨\s*)?Security\s*</code>|"
        r"<code>\s*(?:⚯\s*)?Reliability\s*</code>|"
        r"<code>\s*(?:✓\s*)?Correctness\s*</code>|"
        r"Bug|Rule\s*violation|Security|Reliability|Correctness",
        re.IGNORECASE,
    )

    REGEX_QODO_AGENT_PROMPT = re.compile(
        r"<details>\s*<summary>\s*<strong>\s*Agent Prompt\s*</strong>\s*</summary>\s*```([\s\S]*?)```\s*(?:<code>[\s\S]*?</code>)?\s*</details>",
        re.IGNORECASE,
    )

    REGEX_QODO_ISSUE_DESCRIPTION = re.compile(
        r"## Issue description\s*\n([\s\S]*?)(?=\n## |\Z)",
        re.IGNORECASE,
    )

    REGEX_QODO_ISSUE_CONTEXT = re.compile(
        r"## Issue Context\s*\n([\s\S]*?)(?=\n## |\Z)",
        re.IGNORECASE,
    )

    REGEX_QODO_FIX_FOCUS = re.compile(
        r"## Fix Focus Areas\s*\n([\s\S]*?)(?=\n## |\n<code>|\Z)",
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

    @classmethod
    def parse_qodo_agent_prompt(cls, body: str) -> dict[str, str | None]:
        """
        解析 Qodo Agent Prompt 结构化内容

        Qodo 格式：
        <details>
        <summary><strong>Agent Prompt</strong></summary>

        ```
        ## Issue description
        ...

        ## Issue Context
        ...

        ## Fix Focus Areas
        - file.py[10-20]
        ```
        </details>

        Args:
            body: 评论正文

        Returns:
            {
                "issue_description": str | None,
                "issue_context": str | None,
                "fix_focus_areas": str | None,
            }
        """
        if not body or "Agent Prompt" not in body:
            return {
                "issue_description": None,
                "issue_context": None,
                "fix_focus_areas": None,
            }

        match = cls.REGEX_QODO_AGENT_PROMPT.search(body)
        if not match:
            return {
                "issue_description": None,
                "issue_context": None,
                "fix_focus_areas": None,
            }

        prompt_content = match.group(1)

        issue_desc_match = cls.REGEX_QODO_ISSUE_DESCRIPTION.search(prompt_content)
        issue_context_match = cls.REGEX_QODO_ISSUE_CONTEXT.search(prompt_content)
        fix_focus_match = cls.REGEX_QODO_FIX_FOCUS.search(prompt_content)

        return {
            "issue_description": issue_desc_match.group(1).strip() if issue_desc_match else None,
            "issue_context": issue_context_match.group(1).strip() if issue_context_match else None,
            "fix_focus_areas": fix_focus_match.group(1).strip() if fix_focus_match else None,
        }

    REGEX_SOURCERY_THREAD = re.compile(
        r"\*\*(issue|suggestion|nitpick)(?:\s*\((\w+)\))?:\*\*\s*(.+)",
        re.MULTILINE,
    )

    SOURCERY_TYPE_MAP = {
        "bug_risk": "bug_risk",
        "security": "security",
        "performance": "performance",
        "testing": "testing",
        "typo": "typo",
    }

    @classmethod
    def parse_sourcery_thread_body(cls, body: str) -> dict[str, str | None]:
        """
        解析 Sourcery Thread 评论正文

        格式示例：
        - **issue (bug_risk):** 描述内容
        - **suggestion:** 描述内容
        - **nitpick (typo):** 描述内容

        Args:
            body: 评论正文

        Returns:
            {
                "issue_type": str | None,
                "issue_to_address": str | None,
            }
        """
        if not body:
            return {"issue_type": None, "issue_to_address": None}

        match = cls.REGEX_SOURCERY_THREAD.search(body)
        if not match:
            return {"issue_type": None, "issue_to_address": None}

        category = match.group(1).lower()
        subtype = match.group(2).lower() if match.group(2) else None
        description = match.group(3).strip()

        if subtype and subtype in cls.SOURCERY_TYPE_MAP:
            issue_type = cls.SOURCERY_TYPE_MAP[subtype]
        elif category == "issue":
            issue_type = "bug_risk"
        elif category == "nitpick":
            issue_type = "suggestion"
        else:
            issue_type = category

        return {
            "issue_type": issue_type,
            "issue_to_address": description,
        }
