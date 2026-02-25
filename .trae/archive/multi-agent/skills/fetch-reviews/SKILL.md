---
name: fetch-reviews
description: 获取所有审查机器人评论。Qodo 使用 WebFetch，Sourcery/Copilot 使用 GitHub MCP。
---

# 获取审查意见

## 触发条件

- PR 创建后需要查看审查意见
- 需要检查审查状态

## 仓库信息

| 属性 | 值 |
|------|-----|
| owner | `Disaster-Terminator` |
| repo | `RewardsCore` |

## 获取策略

### Sourcery 和 Copilot

使用 GitHub MCP：

```
get_pull_request_comments(owner, repo, pull_number)
get_pull_request_reviews(owner, repo, pull_number)
```

### Qodo

**获取方法**（两种评论都需要）：

```bash
# 1. Review comments（行级评论）
WebFetch(url="https://api.github.com/repos/{owner}/{repo}/pulls/{number}/comments")

# 2. Issue comments（完整审查报告）
WebFetch(url="https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments")
```

**过滤条件**：`user.login == "qodo-code-review[bot]"`

**解析方法**：

- 提取 `<details><summary><strong>Agent Prompt</strong></summary>` 中的内容
- 问题类型标记：`<s>` 标签表示已解决

**重要**：Qodo 的完整审查报告通常在 Issue comments 中，必须同时获取两种评论。

**失败处理**：如果两种方法都无法获取完整评论：

1. 记录已获取的部分评论
2. 在 Memory MCP 中标记"Qodo 评论可能不完整"
3. 通知人工确认时说明情况

## 解析策略

### Sourcery

1. 过滤 `user.login == "sourcery-ai[bot]"`
2. 提取 `<details><summary>Prompt for AI Agents</summary>` 中的 `~~~markdown` 块
3. 解析 Individual Comments 部分

### Copilot

1. 过滤 `user.login == "copilot-pull-request-reviewer[bot]"`
2. 直接读取 body（纯 Markdown）

### Qodo

1. 过滤 `user.login == "qodo-code-review[bot]"`
2. 解析 `body` 中的 HTML：
   - 提取 `<details><summary><strong>Agent Prompt</strong></summary>` 中的内容
   - 提取 `Fix Focus Areas` 列表
3. 问题类型：
   - 🐞 Bug：必须修复
   - 📘 Rule violation：必须修复
   - ⛨ Security：必须修复
   - 🏯 Reliability：必须修复

## 输出格式

### 审查意见汇总

| 来源 | 类型 | 问题 | 文件 | 状态 |
|------|------|------|------|------|
| Sourcery | bug_risk | ... | ... | 待修复 |
| Copilot | suggestion | ... | ... | 自主决断 |
| Qodo | Bug | ... | ... | 待修复 |

### 解决状态检测

通过检查评论 `body` 判断是否已解决：

| 机器人 | 已解决标志 | 说明 |
|--------|-----------|------|
| Sourcery | `✅ Addressed in {commit}` | 自动更新评论 |
| Copilot | 无 | 不会更新评论，无法判断 |
| Qodo | ✅  | 自动更新评论 |

**示例**：

```
body: "**issue (bug_risk):** ...\n\n✅ Addressed in ab1e26c: ..."
→ 状态：已解决（Sourcery 自动检测）
```

**注意**：Copilot 不会自动更新评论，Agent 无法通过 API 判断其评论是否已解决。需人工在 GitHub 网页上点击"Resolve conversation"。
