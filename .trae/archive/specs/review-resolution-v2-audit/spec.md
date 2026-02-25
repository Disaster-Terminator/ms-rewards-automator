# AI 审查评论解决流程 v2 技术审计 Spec

## Why

在审查 **意见.md** 和 **评论解决流程架构改进计划-v2.md** 后，发现 v2 方案存在 **2 个功能性缺陷** 和 **4 个架构不明确点**。经过技术审计，现已做出最终决策。

## What Changes

- **修正** GraphQL 查询：获取 Thread ID 而非 Comment ID
- **补充** 解决评论的 GitHub GraphQL mutation 调用
- **统一** 数据模型设计：以 Thread 为核心单位（`ReviewThreadState`）
- **实现** 回复功能：使用 GraphQL `addPullRequestReviewThreadReply` mutation
- **明确** 集成方式：Skill 调用 Python CLI
- **增强** Qodo 解析规则：使用严谨的锚点正则

## Impact

- Affected specs: review-comments-resolution
- Affected code:
  - `src/review/graphql_client.py`
  - `src/review/models.py`
  - `src/review/resolver.py`
  - `src/review/parsers.py`
  - `tools/manage_reviews.py` (新建)

## 技术决策记录

### 决策 1：Thread ID vs Comment ID

**决策**：必须使用 **Thread ID**。

**理由**：

- GitHub GraphQL API 的 `resolveReviewThread` mutation 唯一接受的参数是 `threadId` (Base64 Node ID)
- Comment ID 无法用于解决操作

**修正操作**：

```python
reviewThreads(last: 50) {
    nodes {
        id            # ✅ 这是 Thread ID (Node ID)
        isResolved    # ✅ GitHub 上的真实状态
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
```

### 决策 2：API 调用缺失

**决策**：采用 **"API 驱动状态"** 模式。

**理由**：

- 本地数据库仅作为缓存
- 必须先调用 GitHub API 成功，再更新本地 DB
- 确保数据一致性

**修正操作**：

```python
def resolve_thread(self, thread_id: str, resolution_type: str, reply_text: Optional[str] = None):
    # 1. (可选) 回复
    if reply_text:
        self.graphql_client.reply_to_thread(thread_id, reply_text)
    
    # 2. 调用 GitHub API 标记为解决
    is_resolved_remote = self.graphql_client.resolve_thread(thread_id)
    if not is_resolved_remote:
        return {"success": False, "message": "GitHub API failed"}
    
    # 3. 只有 API 成功后，才更新本地 DB
    self.manager.mark_resolved_locally(thread_id, resolution_type)
    return {"success": True}
```

### 决策 3：数据模型设计

**决策**：统一采用 **ReviewThreadState (以线程为核心)**。

**理由**：

- 一个 Review Thread 可能包含多条评论
- "解决状态"是属于 Thread 的属性
- 存 Comment 会导致数据冗余和状态同步困难

**修正操作**：

```python
class ReviewThreadState(BaseModel):
    id: str = Field(..., description="GraphQL Node ID of the Thread")
    is_resolved: bool
    primary_comment_body: str
    comment_url: str
    source: str
    local_status: str = "pending"  # pending, resolved, ignored
    resolution_type: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    last_updated: str
```

### 决策 4：Qodo 解析规则

**决策**：使用 **严谨的锚点正则**。

**理由**：

- 防止正文中的 emoji（如 "Checked ✅ item"）误触发解决状态
- 强制匹配行首 (`^`)
- 兼容 Markdown 列表格式（如 `- ✅ Addressed` 或 `* ☑ ...`）

**修正操作**：

```python
import re

class ReviewParser:
    # ✅ 严格匹配：
    # 1. 行首的 ☑ (U+2611)
    # 2. 行首的 "✅ Addressed" (必须要跟 Addressed，防止普通 emoji)
    # 3. 兼容 Markdown 列表符号 (- 或 *)
    # 4. 忽略大小写
    REGEX_RESOLVED = re.compile(r"^\s*(?:[-*]\s*)?(?:☑|✅\s*Addressed)", re.MULTILINE | re.IGNORECASE)

    @classmethod
    def is_auto_resolved(cls, body: str) -> bool:
        if not body:
            return False
        return bool(cls.REGEX_RESOLVED.search(body))
```

### 决策 5：回复功能实现

**决策**：使用 **GraphQL Mutation** (`addPullRequestReviewThreadReply`)。

**理由**：

- 保持技术栈纯净
- 不回退到 REST API
- 更不回退到 Playwright

**修正操作**：

```python
def reply_to_thread(self, thread_id: str, body: str) -> str:
    mutation = """
    mutation($threadId: ID!, $body: String!) {
      addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
        comment {
          id
        }
      }
    }
    """
    data = self._execute(mutation, {"threadId": thread_id, "body": body})
    return data["addPullRequestReviewThreadReply"]["comment"]["id"]
```

### 决策 6：集成方式

**决策**：**Skill 调用 Python CLI**。

**理由**：

- Agent Skill 本质上是意图定义的入口
- 复杂的业务逻辑（重试、DB操作、API交互）应封装在 Python 脚本中
- 由 Skill 通过 `python tools/manage_reviews.py ...` 调用

**修正操作**：

```markdown
# resolve-review-comment Skill

执行以下步骤：

1. 调用 Python 工具脚本：
   ```bash
   python tools/manage_reviews.py resolve \
     --owner {owner} \
     --repo {repo} \
     --thread-id {thread_id} \
     --type {resolution_type} \
     --reply "Optional reply message"
   ```

1. 返回脚本的 JSON 输出结果。

```

## ADDED Requirements

### Requirement: GraphQL 查询必须返回 Thread ID

系统必须获取 Review Thread 的 Node ID，而非单个评论的 ID。

#### Scenario: 正确获取 Thread ID

- **WHEN** 调用 `fetch_pr_threads` 方法
- **THEN** 返回的每个节点包含 `id` 字段（Thread ID）
- **AND** 返回 `isResolved` 字段
- **AND** 返回 `path` 和 `line` 字段
- **AND** 返回第一条评论的 `body`、`author`、`url`

### Requirement: 解决评论必须调用 GitHub API

系统在解决评论时必须调用 GitHub GraphQL mutation，且遵循 "API First, DB Second" 原则。

#### Scenario: 通过 API 解决评论

- **GIVEN** Thread ID 和 resolution_type
- **WHEN** 调用 `resolve_thread` 方法
- **THEN** 发送 `resolveReviewThread` mutation 到 GitHub
- **AND** 验证返回的 `isResolved` 为 true
- **AND** 更新本地数据库状态
- **AND** 返回成功结果

#### Scenario: API 调用失败时保持数据一致性

- **GIVEN** Thread ID
- **WHEN** GitHub API 调用失败
- **THEN** 抛出异常
- **AND** 本地数据库状态保持不变
- **AND** 记录错误日志

### Requirement: 数据模型以 Thread 为核心单位

系统应使用 `ReviewThreadState` 作为核心数据模型。

#### Scenario: Thread 数据模型定义

- **GIVEN** 一个 Review Thread
- **THEN** 存储以下字段：
  - `id`: Thread 的 GraphQL Node ID
  - `is_resolved`: GitHub 上的解决状态
  - `primary_comment_body`: 第一条评论内容
  - `comment_url`: 评论 URL
  - `source`: 评论来源（Sourcery/Qodo/Copilot）
  - `file_path`: 文件路径
  - `line_number`: 行号
  - `local_status`: 本地处理状态（pending/resolved/ignored）
  - `resolution_type`: 解决依据类型

#### Scenario: 拉取时远端状态覆盖本地状态

- **GIVEN** 本地数据库中某 Thread 的 `local_status` 为 `pending`
- **WHEN** 调用 `fetch_pr_threads` 拉取最新数据
- **AND** GraphQL 返回该 Thread 的 `isResolved` 为 `true`
- **THEN** 强制更新本地该 Thread 的 `local_status` 为 `resolved`
- **AND** `resolution_type` 标记为 `manual_on_github`
- **AND** 记录日志说明状态来源

### Requirement: 回复功能使用 GraphQL Mutation

系统应使用 `addPullRequestReviewThreadReply` mutation 实现回复功能。

#### Scenario: 在 Thread 下回复

- **GIVEN** Thread ID 和回复内容
- **WHEN** 调用 `reply_to_thread` 方法
- **THEN** 发送 `addPullRequestReviewThreadReply` mutation
- **AND** 返回新评论的 ID

### Requirement: Skill 调用 Python CLI

Skill 应作为 Python CLI 的调用包装器。

#### Scenario: resolve-review-comment skill 调用 CLI

- **GIVEN** `resolve-review-comment` skill 被调用
- **WHEN** 执行解决流程
- **THEN** 调用 `python tools/manage_reviews.py resolve ...`
- **AND** 返回脚本的 JSON 输出结果

## MODIFIED Requirements

### Requirement: Qodo 解析规则增强

解析 Qodo 评论状态时，应使用严谨的锚点正则，并兼容 Markdown 列表格式。

#### Scenario: 已解决状态检测

- **GIVEN** Qodo 评论内容
- **WHEN** 检测解决状态
- **THEN** 使用正则 `^\s*(?:[-*]\s*)?(?:☑|✅\s*Addressed)` 匹配
- **AND** 忽略大小写

#### Scenario: 防止误匹配

- **GIVEN** 评论内容包含 "Checked ✅ item"
- **WHEN** 检测解决状态
- **THEN** 不匹配（因为 ✅ 不在行首）
- **AND** 状态保持 pending

#### Scenario: 兼容 Markdown 列表格式

- **GIVEN** 评论内容包含 "- ✅ Addressed in abc1234" 或 "* ☑ Fixed"
- **WHEN** 检测解决状态
- **THEN** 匹配成功
- **AND** 状态标记为 resolved

## REMOVED Requirements

### Requirement: 废弃 Playwright 用于核心操作

**Reason**: GraphQL API 可以完成所有核心操作（获取、解决、回复），无需启动无头浏览器。

**Migration**: 
- 数据获取：使用 GraphQL API
- 评论解决：使用 GraphQL mutation
- 回复功能：使用 GraphQL mutation
- Playwright 仅保留用于 E2E 验收测试中的 UI 验证

## 文件结构

```

src/review/
├── **init**.py
├── models.py              # ReviewThreadState 数据模型
├── parsers.py             # Qodo 解析器（严谨正则）
├── graphql_client.py      # GraphQL 客户端（fetch_pr_threads, resolve_thread, reply_to_thread）
├── comment_manager.py     # TinyDB 状态管理器
└── resolver.py            # 整合器（API First, DB Second）

tools/
└── manage_reviews.py      # CLI 入口（供 Skill 调用）

```
