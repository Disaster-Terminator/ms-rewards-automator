---
name: pr-review
description: PR 审查与自动化交付流程。创建 PR 后触发，处理 AI 审查机器人交互。
---

# PR 审查与自动化交付

## 触发条件

- 创建 PR 后
- 需要触发 AI 审查
- 需要处理审查结果

## AI 审查机器人

| 机器人 | 触发方式 | 可标记解决 | 解决状态检测 |
|--------|---------|-----------|-------------|
| Sourcery | `@sourcery-ai review` | ✅ 自动 | 检查 `body` 含 `✅ Addressed` |
| Copilot | 自动（PR 创建时） | ❌ | 无法判断，需人工处理 |
| Qodo | `/review` | ❌ | 无法判断，需人工处理 |

**解决状态判断**：

- **Sourcery**：会自动更新评论添加 `✅ Addressed in {commit}`
- **Copilot/Qodo**：不会更新评论，Agent 无法通过 API 判断是否已解决

**人工处理**：Copilot/Qodo 评论需在 GitHub 网页上点击"Resolve conversation"。

## Sourcery 命令

| 命令 | 用途 |
|------|------|
| `@sourcery-ai review` | 触发新审查 |
| `@sourcery-ai resolve` | 解决所有评论 |
| `@sourcery-ai dismiss` | 解除所有审查 |

## Qodo 命令

| 命令 | 用途 |
|------|------|
| `/review` | PR 审查 |
| `/describe` | 生成 PR 描述 |
| `/improve` | 代码改进建议 |
| `/compliance` | 合规性检查 |
| `/test` | 生成单元测试 |
| `/implement` | 根据审查建议生成实现代码 |
| `/ask ...` | 自由提问 |

**注意**：Qodo 没有解决评论的命令。

## 审查流程

### 阶段 1：等待审查

1. 创建 PR 后，Copilot 自动开始审查
2. 等待 2 分钟
3. 调用 `get_pull_request_reviews` 检查状态
4. 如果 Sourcery/Qodo 未响应，发送触发命令

### 阶段 2：获取审查意见

调用 `fetch-reviews` skill 获取所有 AI 审查机器人的评论。

### 阶段 3：处理审查结果

| 审查状态 | 判断依据 | 动作 |
|---------|---------|------|
| **阻断** | `CHANGES_REQUESTED` 或含 `bug`/`security`/`critical` | 调用 dev-agent 修复 |
| **建议** | `COMMENTED` 且为代码风格 | 自主决断 |

**处理流程**：

1. Sourcery 阻断问题 → 修复后执行 `@sourcery-ai resolve`
2. Copilot/Qodo 阻断问题 → 修复后 push 新 commit，等待重新审查
3. 已处理但无法标记的评论 → 记录到 Memory MCP，避免重复处理

**错误处理链路**：

```
审查失败 → dev-agent 修复 → 重新触发审查 → 重新获取评论
```

### 阶段 4：合并决策

**重要限制**：项目要求合并前必须解决所有对话。Copilot/Qodo 评论无法标记解决，因此 **Agent 无法自主合并**。

**Agent 职责**：

1. 修复所有阻断问题
2. 确认 CI 通过
3. 记录已处理的评论到 Memory MCP
4. 通知人工确认合并

**人工确认清单**：

- [ ] 所有 `bug`/`security` 问题已修复
- [ ] CI 检查通过
- [ ] 已处理的评论已人工标记解决

## 审查闭环与知识归档流程

### 触发条件

当检测到所有 AI 审查（Sourcery/Qodo）的问题均已标记为 `✅ Addressed` 或被判定为可忽略时，在通知人类进行合并之前，必须执行以下同步操作。

### 执行步骤

#### 1. 提取经验

从 `.trae/current_task.md` 和 `.trae/test_report.md` 中提取本次解决的核心问题：
- DOM 选择器变更
- 反爬策略调整
- 接口变更
- 其他关键修复

#### 2. 强制写入

调用 Memory MCP `create_entities`，以 JSON 格式写入：

```json
{
  "name": "<规则名称>",
  "entityType": "Rewards_Target_Node",
  "observations": [
    "[DOM_Rule] 选择器：<选择器>",
    "[Anti_Bot] 绕过策略：<策略描述>",
    "task_id: <任务ID>",
    "update_date: <更新日期>"
  ]
}
```

#### 3. 结束任务

写入确认成功后：
1. 输出终端信息提醒用户"已就绪，请手动合并 PR"
2. 输出 `[TASK_DONE]` 标签终止流转

### 约束

- 必须在通知人工合并之前执行
- 必须确认 Memory MCP 写入成功
- 必须输出 `[TASK_DONE]` 终止流转
