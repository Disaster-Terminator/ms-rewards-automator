# 评论上下文增强 Spec

## Why

当前评论处理系统存在架构缺陷：`ReviewThreadState`（操作对象）缺少结构化的问题描述，而 `ReviewOverview.prompt_individual_comments`（问题描述）缺少 Thread ID。Agent 需要同时获取两种信息才能有效工作。

## What Changes

- 添加 `EnrichedContext` 模型，将结构化元数据注入到 `ReviewThreadState`
- 实现 Sourcery Prompt → Thread 的映射逻辑（Left Join）
- 实现 Qodo Emoji 类型解析
- 添加 `fetch_issue_comments()` 调用，获取 Qodo PR Reviewer Guide
- 添加 `rich` 库依赖，增强 CLI 表格输出（颜色区分问题严重性）
- 更新 Skill 文档，明确区分"操作对象"与"参考对象"，添加降级策略说明
- 修正归档文档中的已知错误（机器人 ID、Qodo 格式等）

## Impact

- Affected specs: `review-comments-resolution`, `review-resolution-v2-audit`
- Affected code: `src/review/models.py`, `src/review/parsers.py`, `src/review/resolver.py`, `tools/manage_reviews.py`
- Affected skills: `fetch-reviews`, `resolve-review-comment`
- Reference docs: `docs/reference/archive/v1-ai-reviewer-guide.md`（降级策略参考，无需更新）

---

## ADDED Requirements

### Requirement: EnrichedContext 数据模型

系统应提供 `EnrichedContext` 模型，用于存储从摘要或评论正文中提取的结构化元数据。

#### Scenario: EnrichedContext 创建

- **WHEN** 处理审查线程时
- **THEN** 系统应创建可选的 `EnrichedContext`，包含以下字段：
  - `issue_type`: str = "suggestion"（原始类型字符串，可能包含多个类型如 "Bug, Security"）
  - `issue_to_address`: Optional[str] = None（来自 Sourcery Prompt）
  - `code_context`: Optional[str] = None（来自 Sourcery Prompt）

---

### Requirement: Sourcery Prompt 映射

系统应使用 Left Join 策略将 Sourcery Prompt Individual Comments 映射到 Review Threads。

#### Scenario: 成功映射

- **WHEN** Sourcery Prompt Individual Comment 通过 `file_path` + `line_number` 匹配到 Thread
- **AND** Thread 的 `is_resolved=False`
- **THEN** 系统应将 `issue_to_address` 和 `code_context` 注入到 Thread 的 `enriched_context`

#### Scenario: Thread 已解决

- **WHEN** Sourcery Prompt Individual Comment 匹配到 Thread
- **AND** Thread 的 `is_resolved=True`
- **THEN** 系统应跳过此 Thread，尝试查找其他匹配的 Thread

#### Scenario: 未找到匹配 Thread

- **WHEN** Sourcery Prompt Individual Comment 找不到任何 `is_resolved=False` 的匹配 Thread
- **THEN** 系统应丢弃此摘要（Left Join 策略）

#### Scenario: 同一行多个 Thread

- **WHEN** 多个 Thread 匹配相同的 `file_path` + `line_number`
- **AND** 多个 Thread 的 `is_resolved=False`
- **THEN** 系统应只将 `enriched_context` 注入到第一个匹配的 Thread

---

### Requirement: Qodo Emoji 类型解析

系统应解析 Qodo 评论正文，从 Emoji 模式中提取问题类型信息。

#### Scenario: 单类型提取

- **WHEN** Qodo 评论正文包含 `🐞 Bug` 模式
- **THEN** 系统应提取 "Bug" 作为 `issue_type`

#### Scenario: 多类型提取

- **WHEN** Qodo 评论正文包含多个模式如 `🐞 Bug ⛯ Reliability`
- **THEN** 系统应提取 "Bug, Reliability" 作为 `issue_type`

#### Scenario: 无 Emoji

- **WHEN** Qodo 评论正文不包含已识别的 Emoji 模式
- **THEN** 系统应使用默认值 "suggestion"

#### 支持的 Emoji 模式

| Emoji | 类型名称 |
|-------|---------|
| 🐞 | Bug |
| 📘 | Rule violation |
| ⛨ | Security |
| ⚯ | Reliability |
| ✓ | Correctness |

---

### Requirement: Issue Comments 获取

系统应获取 Issue Comments 以获取 Qodo PR Reviewer Guide。

#### Scenario: 获取 Issue Comments

- **WHEN** 调用 `fetch_threads()` 时
- **THEN** 系统应同时调用 `fetch_issue_comments()` 获取 Issue Comments

#### Scenario: 过滤 Qodo PR Reviewer Guide

- **WHEN** 处理 Issue Comments 时
- **AND** 评论作者是 `qodo-code-review bot`
- **AND** 评论正文包含 "PR Reviewer Guide"
- **THEN** 系统应将其存储为 `IssueCommentOverview`，设置 `is_pr_reviewer_guide=True`

#### Scenario: 过滤 Qodo Review Summary

- **WHEN** 处理 Issue Comments 时
- **AND** 评论作者是 `qodo-code-review bot`
- **AND** 评论正文包含 "Review Summary by Qodo"
- **THEN** 系统应将其存储为 `IssueCommentOverview`，设置 `is_code_change_summary=True`

---

### Requirement: CLI 表格输出

系统应使用 `rich` 库提供增强的表格输出，并使用颜色区分问题严重性。

#### Scenario: 列出待处理线程

- **WHEN** 用户运行 `python tools/manage_reviews.py list --status pending`
- **THEN** 系统应显示表格，包含列：
  - ID（缩短显示）
  - Source
  - Status
  - Enriched（如有 `enriched_context` 则显示 ✅ + 类型缩写）
  - Location（file:line）

#### Scenario: 颜色区分问题严重性

- **WHEN** Thread 的 `enriched_context.issue_type` 包含必须修复的类型
- **THEN** 该行应显示为红色
- **WHEN** Thread 的 `enriched_context.issue_type` 仅包含建议类型
- **THEN** 该行应显示为黄色

#### 必须修复的类型

| 类型 | 来源 |
|------|------|
| Bug | Qodo |
| Security | Qodo |
| Rule violation | Qodo |
| Reliability | Qodo |
| bug_risk | Sourcery |
| security | Sourcery |

#### 建议类型

| 类型 | 来源 |
|------|------|
| Correctness | Qodo |
| suggestion | Sourcery |
| performance | Sourcery |

#### Scenario: Enriched 列显示

- **WHEN** Thread 有 `enriched_context`
- **THEN** Enriched 列应显示 "✅" 后跟类型缩写：
  - Bug → "Bug"
  - Security → "Sec"
  - Rule violation → "Rule"
  - Reliability → "Rel"
  - Correctness → "Cor"
  - suggestion → "Sug"

---

### Requirement: 降级策略

系统应在 CLI 工具失败时提供降级方案。

#### Scenario: CLI 工具失败

- **WHEN** CLI 工具执行失败
- **THEN** 系统应提示用户参考 `docs/reference/archive/v1-ai-reviewer-guide.md` 作为降级方案

---

## MODIFIED Requirements

### Requirement: ReviewThreadState 模型

`ReviewThreadState` 模型应包含可选的 `enriched_context` 字段。

```python
class ReviewThreadState(BaseModel):
    id: str
    is_resolved: bool
    primary_comment_body: str
    comment_url: str
    source: str
    file_path: str
    line_number: int
    local_status: str = "pending"
    resolution_type: Optional[str] = None
    enriched_context: Optional[EnrichedContext] = None  # 新增
    last_updated: str
```

### Requirement: ReviewOverview 模型

`ReviewOverview` 模型应移除 `prompt_individual_comments` 字段（已迁移到 Thread）。

**迁移后保留的字段**：

- `id`, `body`, `source`, `url`, `state`, `submitted_at`
- `high_level_feedback`: 保留（总览意见）
- `has_prompt_for_ai`: 保留（快速判断）
- `prompt_overall_comments`: 保留（总览意见）
- `is_code_change_summary`: 保留
- `local_status`: 保留

**移除的字段**：

- `prompt_individual_comments`: 已迁移到 `ReviewThreadState.enriched_context`

### Requirement: IssueCommentOverview 模型

`IssueCommentOverview` 模型应移除 `local_status` 字段，定义为纯只读参考文档。

**理由**：PR Reviewer Guide 不需要"解决"，只需要阅读。Agent 工作流已经足够复杂，不需要额外的"确认"操作。

### Requirement: 归档文档修正

`docs/reference/archive/v1-ai-reviewer-guide.md` 需要修正已知错误，确保正确反映三种机器人的审查评论格式和规律。

#### 需要修正的内容

| 修正项 | 原内容 | 正确内容 |
|--------|--------|----------|
| 机器人 ID | 缺失 | 添加 Sourcery (`sourcery-ai bot`)、Copilot (`Copilot AI`)、Qodo (`qodo-code-review bot`) |
| Qodo 行级评论格式 | `1. cli.py prints raw exception ☑ 📘 Rule violation` | `1. cli.py prints raw exception 📘 Rule violation`（移除错误的 ☑） |
| Code Review by Qodo API 返回 | "❌ 截断" | "❌ **空字符串**" |
| 行级评论格式说明 | 缺失 | 添加：`编号. 问题标题 Emoji类型...` |

**注意**：归档文档记录的是固定知识（三种机器人的格式规律），修正后不需要随版本更新。

---

## REMOVED Requirements

### Requirement: prompt_individual_comments in ReviewOverview

**原因**: 数据迁移到 `ReviewThreadState.enriched_context`，消除冗余。

**迁移**: `overviews` 命令应从 Thread 数据重建 individual comments 输出。

### Requirement: IssueCommentOverview.local_status

**原因**: IssueCommentOverview 定义为纯只读参考文档，不需要状态追踪。

---

## 处理建议汇总

| 评论类型 | Agent 行为 |
|----------|------------|
| `bug_risk`, `Bug`, `Security`, `Rule violation`, `Reliability` | 报告给用户，等待修复指令（红色） |
| `suggestion`, `performance`, `Correctness` | 报告给用户，自主决断是否采纳（黄色） |
| PR Reviewer Guide 🔍 | 直接报告给用户（改进意见摘要） |
| Reviewer's Guide (Sourcery) | 仅作参考（代码变化摘要，非改进意见） |
| Review Summary by Qodo | 仅作参考（代码变化摘要，非改进意见） |

---

## 严禁事项

1. **严禁一次性解决所有评论**：每个评论必须单独处理
2. **严禁无依据标记解决**：必须先确认问题已解决
3. **严禁批量操作**：必须逐个评论处理
4. **严禁跳过说明评论**：rejected/false_positive 必须回复
