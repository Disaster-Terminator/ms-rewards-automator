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
| `[REQ_DEV]` | 读取 `.trae/test_report.md`，唤醒 dev-agent，附带上下文 |
| `[REQ_DOCS]` | 唤醒 docs-agent |
| `[BLOCK_NEED_MASTER]` | 读取 `.trae/blocked_reason.md`，做出决策 |

## Memory MCP 读写时机

### 读取时机

| 时机 | 操作 | 内容 |
|------|------|------|
| 任务分发前 | `search_nodes` | 检索 `[REWARDS_DOM]` 或 `[ANTI_BOT]` 规则 |

### 写入时机

| 时机 | 操作 | 内容 |
|------|------|------|
| PR 合并后 | `create_entities` | 总结页面规则，使用标签归档 |

### 写入格式

```json
{
  "name": "<规则名称>",
  "entityType": "Component",
  "observations": [
    "[REWARDS_DOM] 选择器：#search-btn-v2",
    "[ANTI_BOT] Cloudflare 绕过策略：等待 5 秒"
  ]
}
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
| `fetch-reviews` | `pr-review` 内部调用 | 获取 Sourcery/Copilot/Qodo 评论 |

**注意**：
- `fetch-reviews` 由 `pr-review` 内部调用，无需单独调用
- 项目要求合并前解决所有对话，Copilot/Qodo 评论无法标记解决，因此 **合并需人工确认**

## 合并限制

项目要求合并前必须解决所有对话：

- **Sourcery**：自动检测 `✅ Addressed`
- **Copilot/Qodo**：无法通过 API 标记解决，需人工在 GitHub 网页点击"Resolve conversation"

**结论**：Agent 无法自主合并 PR，需人工确认。
