from review.models import EnrichedContext, ReviewThreadState
from review.resolver import ReviewResolver


class TestInjectSourceryTypes:
    """测试 _inject_sourcery_types 方法"""

    def _create_resolver(self):
        return ReviewResolver(token="fake-token", owner="test", repo="test")

    def test_inject_bug_risk(self):
        """测试注入 bug_risk 类型"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="**issue (bug_risk):** Using the package's own name",
            comment_url="https://example.com",
            source="Sourcery",
        )

        result = resolver._inject_sourcery_types([thread])
        assert result[0].enriched_context is not None
        assert result[0].enriched_context.issue_type == "bug_risk"
        assert "Using the package's own name" in result[0].enriched_context.issue_to_address

    def test_inject_suggestion(self):
        """测试注入 suggestion 类型"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="**suggestion:** 配置加载异常时同时使用 print",
            comment_url="https://example.com",
            source="Sourcery",
        )

        result = resolver._inject_sourcery_types([thread])
        assert result[0].enriched_context is not None
        assert result[0].enriched_context.issue_type == "suggestion"

    def test_no_injection_for_non_sourcery(self):
        """测试非 Sourcery Thread 不注入"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="Some Qodo comment",
            comment_url="https://example.com",
            source="Qodo",
        )

        result = resolver._inject_sourcery_types([thread])
        assert result[0].enriched_context is None

    def test_no_injection_for_already_enriched(self):
        """测试已有 enriched_context 不覆盖"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="**issue (bug_risk):** Test",
            comment_url="https://example.com",
            source="Sourcery",
            enriched_context=EnrichedContext(issue_type="existing_type"),
        )

        result = resolver._inject_sourcery_types([thread])
        assert result[0].enriched_context.issue_type == "existing_type"


class TestInjectQodoTypes:
    """测试 _inject_qodo_types 方法"""

    def _create_resolver(self):
        return ReviewResolver(token="fake-token", owner="test", repo="test")

    def test_inject_qodo_types(self):
        """测试注入 Qodo 类型"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="""<code>📘 Rule violation</code> <code>⛨ Security</code>

<pre>
ReviewResolver directly returns exception text.
</pre>

<details>
<summary><strong>Agent Prompt</strong></summary>

```
## Issue description
ReviewResolver returns raw exception strings.

## Fix Focus Areas
- src/review/resolver.py[171-173]
```

</details>""",
            comment_url="https://example.com",
            source="Qodo",
        )

        result = resolver._inject_qodo_types([thread])
        assert result[0].enriched_context is not None
        assert "Rule violation" in result[0].enriched_context.issue_type
        assert "Security" in result[0].enriched_context.issue_type
        assert result[0].enriched_context.issue_to_address is not None

    def test_no_injection_for_non_qodo(self):
        """测试非 Qodo Thread 不注入"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="Some Sourcery comment",
            comment_url="https://example.com",
            source="Sourcery",
        )

        result = resolver._inject_qodo_types([thread])
        assert result[0].enriched_context is None

    def test_no_injection_for_already_enriched(self):
        """测试已有 enriched_context 不覆盖"""
        resolver = self._create_resolver()
        thread = ReviewThreadState(
            id="test-id",
            is_resolved=False,
            primary_comment_body="<code>Bug</code>",
            comment_url="https://example.com",
            source="Qodo",
            enriched_context=EnrichedContext(issue_type="existing_type"),
        )

        result = resolver._inject_qodo_types([thread])
        assert result[0].enriched_context.issue_type == "existing_type"
