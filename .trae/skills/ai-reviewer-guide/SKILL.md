---
name: ai-reviewer-guide
description: AI审查工具参考指南。提供Sourcery/Copilot/Qodo的评论类型、解决状态检测、交互命令等详细信息。
---

# AI 审查工具参考指南

## Sourcery

### 评论结构

```
reviews.body 结构：
├── 总览意见（Overall Comments）- 无解决状态
│   └── "In MSRewardsApp.__init__ the diagnosis_reporter..."
└── <details><summary>Prompt for AI Agents</summary>
    └── ## Individual Comments
        ├── ### Comment 1
        │   ├── <location> `file.py:42` </location>
        │   └── <issue_to_address>问题描述</issue_to_address>
        └── ### Comment 2
            └── ...
```

### 类型判断

| 标签 | 含义 | 处理方式 |
|------|------|----------|
| `bug_risk` | 潜在 Bug | 必须修复 |
| `security` | 安全问题 | 必须修复 |
| `suggestion` | 代码建议 | 自主决断 |
| `performance` | 性能建议 | 自主决断 |

### 解决状态检测

- **已解决**：body 含 `✅ Addressed in {commit}`
- **数据源**：`get_pull_request_comments` 返回的行级评论

### 交互命令

| 命令 | 用途 |
|------|------|
| `@sourcery-ai review` | 触发新审查 |
| `@sourcery-ai resolve` | 解决所有评论 |
| `@sourcery-ai dismiss` | 关闭所有审查 |

---

## Qodo

### 审查机制（重要）

| 评论类型 | 触发时机 | 后续行为 |
|----------|----------|----------|
| **Code Review by Qodo** | PR 创建时自动生成 | 只更新解决状态（☑），不发送新评论 |
| **PR Reviewer Guide 🔍** | 第一次 `/review` 斜杠命令 | 后续 `/review` 更新它 |
| **Persistent review updated** | 后续 `/review` 斜杠命令 | 通知评论 |

### 评论类型

| 类型 | 内容 | 触发方式 | API返回 |
|------|------|----------|---------|
| **Code Review by Qodo** | 问题列表（Bug/Rule violation等） | PR创建时自动 | ❌ 截断 |
| **PR Reviewer Guide 🔍** | 审查指南（工作量、安全、重点区域） | 首次 `/review` | ❌ 无 |
| **Persistent review updated** | 更新通知 | 后续 `/review` | ✅ 有 |

### 特征标记

| 标记 | 类型 | 处理方式 |
|------|------|----------|
| 🐞 Bug | Bug | 必须修复 |
| 📘 Rule violation | 规则违反 | 必须修复 |
| ⛨ Security | 安全问题 | 必须修复 |
| ⚯ Reliability | 可靠性问题 | 必须修复 |
| Correctness | 正确性问题 | 自主决断 |

### 解决状态检测

**Code Review by Qodo**：

- **已解决**：评论行开头有 `☑ ☑ ☑ ☑ ☑`（5个勾，注意有空格）
- **重要**：`✓` 符号是类型前缀（如 `✓ Correctness`），不是已解决标志！
- 解决状态会实时更新，但不会发送新评论

**PR Reviewer Guide 🔍**：

- 不包含具体问题，只是审查指南
- 直接报告给用户

### 获取最新审查的流程

1. 使用 Playwright 导航到 PR 页面
2. 找到 "Code Review by Qodo" 评论（查看问题列表和解决状态）
3. 点击 "View more" 展开所有问题
4. 找到 "PR Reviewer Guide 🔍" 评论（查看审查指南）
5. 检查是否有 "Persistent review updated" 通知（确认 PR Reviewer Guide 已更新）

### 交互命令

| 命令 | 用途 |
|------|------|
| `/review` | PR 审查（首次生成 PR Reviewer Guide，后续更新它） |
| `/describe` | 生成 PR 描述 |
| `/improve` | 代码建议 |
| `/checks ci_job` | CI 反馈 |

---

## Copilot

### 类型判断

| 类型 | 处理方式 |
|------|----------|
| 代码建议块（```suggestion） | 自主决断 |
| 安全警告 | 必须修复 |

### 解决状态检测

- 无自动解决状态
- 需人工在 GitHub 网页标记解决

### 交互命令

- 无命令交互，自动审查

---

## 处理建议汇总

| 评论类型 | Agent 行为 |
|----------|------------|
| `bug_risk`, `Bug`, `Security`, `Rule violation`, `Reliability` | 报告给用户，等待修复指令 |
| `suggestion`, `performance`, `Correctness` | 报告给用户，自主决断是否采纳 |
| PR Reviewer Guide | 直接报告给用户 |

## 合并提醒

- **Agent 不自动合并 PR**，需通知用户确认
- Sourcery 可用 `@sourcery-ai resolve` 批量解决
- Copilot/Qodo 需人工处理
