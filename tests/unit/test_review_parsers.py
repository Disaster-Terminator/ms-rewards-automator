from review.models import EnrichedContext, ReviewMetadata, ReviewThreadState
from review.parsers import ReviewParser


class TestReviewParser:
    """测试 Qodo 解析器"""

    def test_is_auto_resolved_with_checkbox(self):
        """测试 ☑ 符号检测"""
        body = "☑ This issue has been resolved"
        assert ReviewParser.is_auto_resolved(body) is True

    def test_is_auto_resolved_with_addressed(self):
        """测试 ✅ Addressed 检测"""
        body = "✅ Addressed in abc1234"
        assert ReviewParser.is_auto_resolved(body) is True

    def test_is_auto_resolved_with_markdown_list_dash(self):
        """测试 Markdown 列表格式（- 符号）"""
        body = "- ✅ Addressed in abc1234"
        assert ReviewParser.is_auto_resolved(body) is True

    def test_is_auto_resolved_with_markdown_list_asterisk(self):
        """测试 Markdown 列表格式（* 符号）"""
        body = "* ☑ Fixed"
        assert ReviewParser.is_auto_resolved(body) is True

    def test_is_auto_resolved_with_emoji_in_middle(self):
        """测试 emoji 在正文中间不应匹配"""
        body = "Checked ✅ item"
        assert ReviewParser.is_auto_resolved(body) is False

    def test_is_auto_resolved_with_empty_body(self):
        """测试空内容"""
        assert ReviewParser.is_auto_resolved("") is False
        assert ReviewParser.is_auto_resolved(None) is False

    def test_is_auto_resolved_case_insensitive(self):
        """测试大小写不敏感"""
        body = "✅ ADDRESSED in abc1234"
        assert ReviewParser.is_auto_resolved(body) is True

    def test_detect_source_sourcery(self):
        """测试 Sourcery 来源检测"""
        assert ReviewParser.detect_source("sourcery-ai") == "Sourcery"
        assert ReviewParser.detect_source("Sourcery") == "Sourcery"

    def test_detect_source_qodo(self):
        """测试 Qodo 来源检测"""
        assert ReviewParser.detect_source("qodo-ai") == "Qodo"
        assert ReviewParser.detect_source("codium") == "Qodo"

    def test_detect_source_copilot(self):
        """测试 Copilot 来源检测"""
        assert ReviewParser.detect_source("copilot") == "Copilot"
        assert ReviewParser.detect_source("Copilot") == "Copilot"

    def test_detect_source_unknown(self):
        """测试未知来源"""
        assert ReviewParser.detect_source("some-user") == "Unknown"
        assert ReviewParser.detect_source("") == "Unknown"

    def test_parse_status_github_resolved(self):
        """测试 GitHub 已解决状态优先"""
        body = "Some pending content"
        assert ReviewParser.parse_status(body, is_resolved_on_github=True) == "resolved"

    def test_parse_status_text_resolved(self):
        """测试文本标记已解决"""
        body = "☑ Fixed"
        assert ReviewParser.parse_status(body, is_resolved_on_github=False) == "resolved"

    def test_parse_status_pending(self):
        """测试待处理状态"""
        body = "This is a bug risk"
        assert ReviewParser.parse_status(body, is_resolved_on_github=False) == "pending"


class TestQodoTypeParsing:
    """测试 Qodo 类型解析"""

    def test_parse_single_bug(self):
        """测试单类型 Bug"""
        body = "3. Ci依赖安装会失效 Bug"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert result == "Bug"

    def test_parse_multiple_types(self):
        """测试多类型"""
        body = "1. cli.py prints raw exception Rule violation Security"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert result == "Rule violation, Security"

    def test_parse_bug_and_reliability(self):
        """测试 Bug + Reliability"""
        body = "Bug Reliability issue here"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert result == "Bug, Reliability"

    def test_parse_correctness(self):
        """测试 Correctness"""
        body = "Correctness issue here"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert result == "Correctness"

    def test_parse_no_type_returns_suggestion(self):
        """测试无类型返回 suggestion"""
        body = "Some random text without type keywords"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert result == "suggestion"

    def test_parse_empty_body(self):
        """测试空内容"""
        assert ReviewParser.parse_qodo_issue_types("") == "suggestion"
        assert ReviewParser.parse_qodo_issue_types(None) == "suggestion"

    def test_parse_case_insensitive(self):
        """测试大小写不敏感"""
        body = "BUG and SECURITY issue"
        result = ReviewParser.parse_qodo_issue_types(body)
        assert "Bug" in result
        assert "Security" in result


class TestEnrichedContext:
    """测试 EnrichedContext 模型"""

    def test_create_enriched_context_default(self):
        """测试默认值"""
        ctx = EnrichedContext()
        assert ctx.issue_type == "suggestion"
        assert ctx.issue_to_address is None
        assert ctx.code_context is None

    def test_create_enriched_context_with_values(self):
        """测试带值创建"""
        ctx = EnrichedContext(
            issue_type="Bug, Security",
            issue_to_address="Fix the security vulnerability",
            code_context="def unsafe_function():",
        )
        assert ctx.issue_type == "Bug, Security"
        assert ctx.issue_to_address == "Fix the security vulnerability"
        assert ctx.code_context == "def unsafe_function():"


class TestReviewThreadState:
    """测试数据模型"""

    def test_create_thread_state(self):
        """测试创建线程状态"""
        thread = ReviewThreadState(
            id="MDI0OlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkMTIz",
            is_resolved=False,
            primary_comment_body="Test comment",
            comment_url="https://github.com/owner/repo/pull/1#discussion_r123",
            source="Sourcery",
        )

        assert thread.id == "MDI0OlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkMTIz"
        assert thread.is_resolved is False
        assert thread.local_status == "pending"
        assert thread.source == "Sourcery"

    def test_thread_state_defaults(self):
        """测试默认值"""
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="",
            comment_url="",
            source="Unknown",
        )

        assert thread.local_status == "pending"
        assert thread.file_path == ""
        assert thread.line_number is None  # 默认是 None，不是 0
        assert thread.resolution_type is None
        assert thread.enriched_context is None

    def test_thread_state_with_enriched_context(self):
        """测试带 enriched_context 的线程"""
        ctx = EnrichedContext(issue_type="Bug", issue_to_address="Fix this bug")
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="Bug here",
            comment_url="https://example.com",
            source="Qodo",
            enriched_context=ctx,
        )

        assert thread.enriched_context is not None
        assert thread.enriched_context.issue_type == "Bug"
        assert thread.enriched_context.issue_to_address == "Fix this bug"


class TestReviewMetadata:
    """测试元数据模型"""

    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = ReviewMetadata(pr_number=123, owner="test-owner", repo="test-repo")

        assert metadata.pr_number == 123
        assert metadata.owner == "test-owner"
        assert metadata.repo == "test-repo"
        assert metadata.version == "2.2"
        assert metadata.etag_comments is None


class TestSourceryThreadParsing:
    """测试 Sourcery Thread 正文解析"""

    def test_parse_issue_with_bug_risk(self):
        """测试 issue (bug_risk) 格式"""
        body = "**issue (bug_risk):** Using the package's own name with extras in dev dependencies"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "bug_risk"
        assert "Using the package's own name" in result["issue_to_address"]

    def test_parse_issue_without_subtype(self):
        """测试 issue 无子类型"""
        body = "**issue:** 文档中对终端工具是否可用的描述前后矛盾"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "bug_risk"
        assert "文档中对终端工具" in result["issue_to_address"]

    def test_parse_suggestion(self):
        """测试 suggestion 格式"""
        body = "**suggestion:** 配置加载异常时同时使用 print 和 sys.exit"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "suggestion"
        assert "配置加载异常时" in result["issue_to_address"]

    def test_parse_nitpick_with_typo(self):
        """测试 nitpick (typo) 格式"""
        body = "**nitpick (typo):** fixtures 注释中的中文用词建议从固件改为测试夹具"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "typo"
        assert "fixtures 注释中的中文" in result["issue_to_address"]

    def test_parse_nitpick_without_subtype(self):
        """测试 nitpick 无子类型"""
        body = "**nitpick:** The total_result type annotation doesn't match"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "suggestion"

    def test_parse_suggestion_with_testing(self):
        """测试 suggestion (testing) 格式"""
        body = "**suggestion (testing):** Session-scoped account fixtures may introduce coupling"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] == "testing"

    def test_parse_empty_body(self):
        """测试空内容"""
        assert ReviewParser.parse_sourcery_thread_body("") == {
            "issue_type": None,
            "issue_to_address": None,
        }
        assert ReviewParser.parse_sourcery_thread_body(None) == {
            "issue_type": None,
            "issue_to_address": None,
        }

    def test_parse_no_match(self):
        """测试无匹配格式"""
        body = "This is just a regular comment without Sourcery format"
        result = ReviewParser.parse_sourcery_thread_body(body)
        assert result["issue_type"] is None
        assert result["issue_to_address"] is None


class TestQodoAgentPromptParsing:
    """测试 Qodo Agent Prompt 解析"""

    def test_parse_full_prompt(self):
        """测试完整 Agent Prompt 解析"""
        body = """<img src="https://www.qodo.ai/wp-content/uploads/2025/12/v2-action-required.svg" height="20" alt="Action required">

1. Resolver returns raw exceptions <code>📘 Rule violation</code> <code>⛨ Security</code>

<pre>
ReviewResolver directly returns exception text in the user-facing message field.
</pre>

<details>
<summary><strong>Agent Prompt</strong></summary>

```
## Issue description
ReviewResolver returns raw exception strings in the user-facing message field.

## Issue Context
Compliance requires user-facing errors to be generic.

## Fix Focus Areas
- src/review/resolver.py[171-173]
- src/review/resolver.py[297-310]
```

<code>ⓘ Copy this prompt and use it to remediate the issue</code>
</details>"""
        result = ReviewParser.parse_qodo_agent_prompt(body)
        assert result["issue_description"] is not None
        assert "raw exception strings" in result["issue_description"]
        assert result["issue_context"] is not None
        assert "Compliance requires" in result["issue_context"]
        assert result["fix_focus_areas"] is not None
        assert "src/review/resolver.py" in result["fix_focus_areas"]

    def test_parse_no_agent_prompt(self):
        """测试无 Agent Prompt"""
        body = "This is a regular comment without Agent Prompt"
        result = ReviewParser.parse_qodo_agent_prompt(body)
        assert result["issue_description"] is None
        assert result["issue_context"] is None
        assert result["fix_focus_areas"] is None

    def test_parse_empty_body(self):
        """测试空内容"""
        assert ReviewParser.parse_qodo_agent_prompt("") == {
            "issue_description": None,
            "issue_context": None,
            "fix_focus_areas": None,
        }
        assert ReviewParser.parse_qodo_agent_prompt(None) == {
            "issue_description": None,
            "issue_context": None,
            "fix_focus_areas": None,
        }
