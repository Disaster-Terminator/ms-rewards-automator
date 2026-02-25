---
name: master-execution
description: Master Agent 执行详细流程。任务路由、PR 管理、Git 操作。
---

# Master Agent 执行详细流程

## 触发条件

- 用户发起任务请求
- 收到子 Agent 的状态标签

## 任务分发流程

### 1. 写入任务上下文

将任务细节写入 `.trae/current_task.md`：

```markdown
---
task_id: <唯一ID>
created_at: <时间戳>
type: dev | test | docs
dev_retry_count: 0
max_retries: 3
status: pending
---

### 任务描述

<具体任务内容>

### 上下文信息

- 相关文件：<文件列表>
- 历史规则：<从 Memory MCP 检索的内容>
```

### 2. 检索历史知识

```
使用 Memory MCP search_nodes 检索相关规则
检索标签：[REWARDS_DOM], [ANTI_BOT]
将检索结果附加到任务上下文
```

### 3. 唤醒子 Agent

根据任务类型输出对应标签：

| 任务类型 | 输出标签 |
|----------|----------|
| 代码修改 | `[REQ_DEV]` + `.trae/current_task.md` 路径 |
| 测试验收 | `[REQ_TEST]` + `.trae/current_task.md` 路径 |
| 文档更新 | `[REQ_DOCS]` + `.trae/current_task.md` 路径 |

## 状态标签响应规则

| 收到标签 | 响应动作 |
|----------|----------|
| `[REQ_TEST]` | 唤醒 test-agent，发送 `.trae/current_task.md` 路径 |
| `[REQ_DEV]` | 检查熔断器 → 执行微提交保护 → 唤醒 dev-agent |
| `[REQ_DOCS]` | 检查 docs-agent 触发条件 → 唤醒 docs-agent 或跳过 |
| `[BLOCK_NEED_MASTER]` | 调用 `master-recovery` skill |

## 熔断器检查流程

### 1. 读取重试计数

读取 `.trae/current_task.md` 中的 `dev_retry_count` 和 `max_retries`。

### 2. 判断是否触发熔断

| 条件 | 动作 |
|------|------|
| `dev_retry_count >= max_retries` | **禁止路由**，写入 `blocked_reason.md`，设置 `reason_type: retry_exhausted`，通知人类开发者 |
| `dev_retry_count < max_retries` | 递增 `dev_retry_count`，继续路由 |

### 3. 更新任务状态

覆写 `.trae/current_task.md`，更新 `dev_retry_count` 字段。

## 微提交保护流程

### 1. 触发时机

当 Master Agent 收到 `[REQ_DEV]` 标签（测试失败需重写）时，必须在路由前执行保护操作。

### 2. 执行保护

```bash
# 检查是否有未提交修改
git status --porcelain

# 策略选择
if [有未暂存修改]; then
    git stash push -m "pre-fix state"
elif [有已暂存修改]; then
    git commit -m "WIP: pre-fix state before retry #N"
fi
```

### 3. 确保回滚能力

保护操作完成后，确保可以随时回滚：

```bash
git stash pop  # 或
git reset --hard HEAD~1
```

## Memory MCP 读写时机

### 读取时机

| 时机 | 操作 | 内容 |
|------|------|------|
| 任务分发前 | `search_nodes` | 检索 `[REWARDS_DOM]` 或 `[ANTI_BOT]` 规则 |

### 写入时机

| 时机 | 操作 | 内容 |
|------|------|------|
| PR 合并后 | `create_entities` | 总结页面规则，使用标签归档 |

### 写入契约（结构化格式）

```json
{
  "name": "<规则名称>",
  "entityType": "Component",
  "observations": [
    "[REWARDS_DOM] 选择器：#search-btn-v2",
    "[ANTI_BOT] Cloudflare 绕过策略：等待 5 秒",
    "trigger_date: 202x-xx-xx",
    "old_selector: #sb_form_go",
    "new_selector: #sb_form_q"
  ]
}
```

## docs-agent 确定性触发算法

### 触发条件（满足其一即输出 `[REQ_DOCS]`）

#### 1. 接口级变更

执行 `git diff HEAD~1`，若新增内容包含正则表达式 `^\+\s*(def|class)\s+`。

**检测命令**：
```bash
git diff HEAD~1 | grep -E "^\+.*def |^\+.*class "
```

#### 2. 配置级变更

变更文件列表中包含以下任一文件：
- `.env.example`
- `config.yaml`
- `requirements.txt`
- `pyproject.toml`

**检测命令**：
```bash
git diff HEAD~1 --name-only | grep -E "\.env\.example|config\.yaml|requirements\.txt|pyproject\.toml"
```

#### 3. 依赖级变更

引入了新的第三方库。

**检测命令**：
```bash
git diff HEAD~1 pyproject.toml | grep -E "^\+.*[a-zA-Z0-9_-]+ ="
```

### 跳过条件

若不满足上述任一条件，跳过 `[REQ_DOCS]`，直接进入 PR 创建阶段。

### 执行流程

```
测试全绿
    │
    ▼
执行 Git Diff 检测
    │
    ├─► 满足触发条件 → 输出 [REQ_DOCS]
    │
    └─► 不满足条件 → 跳过，直接创建 PR
```

## Git 规范

**目标**：保持历史整洁，避免碎片化 commit 导致其他分支变基困难。

### 提交策略

| 场景 | 操作 |
|------|------|
| 全新改动 | `git commit -m "message"` |
| 对上次 commit 的修正/补充 | `git commit --amend` |

### amend 用法

```bash
# 修正内容 + 修改信息
git commit --amend -m "新信息"

# 修正内容，保持原信息
git commit --amend --no-edit
```

### 时序

1. 任务完成 → commit
2. 发现需要修正 → amend（未 push 时）
3. 确认无误 → push

## 子 Agent 调用

| Agent | 场景 | 说明 |
|-------|------|------|
| `dev-agent` | 代码修改 | 业务代码编写与局部验证 |
| `test-agent` | 测试验收 | 全量测试与 E2E 验收 |
| `docs-agent` | 文档更新 | README/CHANGELOG 同步 |

**注意**：Master Agent 没有 Playwright MCP，所有 E2E 测试必须交给 test-agent。

## Skills 调用

| Skill | 时机 | 说明 |
|-------|------|------|
| `mcp-acceptance` | 代码修改完成后 | 执行 7 阶段验收 |
| `pr-review` | PR 创建后 | 处理 AI 审查，通知人工合并 |
| `master-recovery` | 收到 `[BLOCK_NEED_MASTER]` | 处理挂起任务恢复 |
| `fetch-reviews` | `pr-review` 内部调用 | 获取 Sourcery/Copilot/Qodo 评论 |

**注意**：
- `fetch-reviews` 由 `pr-review` 内部调用，无需单独调用
- 项目要求合并前解决所有对话，Copilot/Qodo 评论无法标记解决，因此 **合并需人工确认**

## 合并限制

项目要求合并前必须解决所有对话：

- **Sourcery**：自动检测 `✅ Addressed`
- **Copilot/Qodo**：无法通过 API 标记解决，需人工在 GitHub 网页点击"Resolve conversation"

**结论**：Agent 无法自主合并 PR，需人工确认。

## Memory MCP 归档流程

### 触发时机

PR 状态变为 `Merged` 后，切回 `main` 分支前。

### 执行步骤

1. 提取 `current_task.md` 的最终状态
2. 构建结构化 JSON 实体
3. 调用 `create_entities` 写入 Memory MCP

### 写入契约（JSON Schema）

```json
{
  "name": "<规则名称>",
  "entityType": "Rewards_Target_Node",
  "observations": [
    "[DOM_Rule] 选择器：<选择器>",
    "[Anti_Bot] 绕过策略：<策略描述>",
    "task_id: <任务ID>",
    "target_element: <目标元素>",
    "effective_locator: <有效定位器>",
    "obsolete_locator: <废弃定位器>",
    "bypassing_strategy: <绕过策略>",
    "update_date: <更新日期>"
  ]
}
```

### 示例

```json
{
  "name": "Search_Input_Box",
  "entityType": "Rewards_Target_Node",
  "observations": [
    "[DOM_Rule] 选择器：input#sb_form_q",
    "[Anti_Bot] 绕过策略：等待 3 秒以规避动态 DOM 渲染",
    "task_id: req-001",
    "target_element: Search Input Box",
    "effective_locator: input#sb_form_q",
    "obsolete_locator: input#sb_form_go",
    "bypassing_strategy: 等待 3 秒以规避动态 DOM 渲染",
    "update_date: 202x-xx-xx"
  ]
}
```

### 约束

- 必须在 PR 合并后执行
- 必须使用结构化格式
- 必须包含必要的标签（DOM_Rule, Anti_Bot）

## 路由决策树 (Test Success)

当 test-agent 返回全部测试通过后，按以下优先级进行下一步路由：

### 1. 人工强制覆写（最高优先级）

- **条件**：用户明确要求"更新文档"
- **动作**：跳过所有检测，直接输出 `[REQ_DOCS]`

### 2. 系统静态检测

#### 2.1 配置文件检测

执行命令：
```bash
git diff HEAD~1 --name-only
```

检查输出文件列表。若包含以下任一文件，输出 `[REQ_DOCS]`：
- `*.md`（除 `.trae/` 目录下）
- `.env.example`
- `config.yaml`
- `requirements.txt`
- `pyproject.toml`

#### 2.2 接口变更检测

执行命令：
```bash
git diff HEAD~1 -U0 | grep '^\+\s*\(def\|class\)'
```

若终端有输出（证明有新增函数/类），输出 `[REQ_DOCS]`。

### 3. 默认放行

若以上条件均不满足：
- 进入 PR 创建流程
- 或输出 `[TASK_DONE]` 结束任务

### 决策流程图

```
测试全绿
    │
    ├─► 用户要求更新文档？ ──是──► [REQ_DOCS]
    │
    │   否
    │   │
    │   ▼
    ├─► 配置文件变更？ ──是──► [REQ_DOCS]
    │
    │   否
    │   │
    │   ▼
    ├─► 新增 def/class？ ──是──► [REQ_DOCS]
    │
    │   否
    │   │
    │   ▼
    └─► 创建 PR 或 [TASK_DONE]
```
