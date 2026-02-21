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

| 机器人 | 触发方式 | Agent 可控 |
|--------|---------|-----------|
| Copilot | 自动（PR 创建时） | ❌ 无法手动触发 |
| Sourcery | `@sourcery-ai review` | ✅ 可通过评论触发 |
| Qodo | `/review` | ✅ 可通过评论触发 |

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
| `/ask ...` | 自由提问 |

## 审查流程

### 阶段 1：等待审查

1. 创建 PR 后，Copilot 自动开始审查
2. 等待 5 分钟
3. 调用 `get_pull_request_reviews` 检查状态
4. 如果 Sourcery/Qodo 未响应，发送触发命令

### 阶段 2：处理审查结果

| 审查状态 | 判断依据 | 动作 |
|---------|---------|------|
| **阻断** | `CHANGES_REQUESTED` 或含 `bug`/`security`/`critical` | 调用 dev-agent 修复 |
| **建议** | `COMMENTED` 且为代码风格 | 自主决断 |

### 阶段 3：合并决策

**合并条件**：

- CI 检查通过
- 无未解决的 `CHANGES_REQUESTED`
- 至少 1 个 AI 机器人 `APPROVED`

**执行规则**：

| PR 类型 | 合并方式 |
|---------|---------|
| 常规 Bugfix/Feature | 自动合并 |
| 核心/大规模变更 | 等待人工确认 |
