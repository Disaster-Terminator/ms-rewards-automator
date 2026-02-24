---
name: request-reviews
description: |
  申请新的 AI 审查评论（独立 Skill）。
  触发：用户说"申请新审查"、"重新审查"、"触发审查"时。
  注意：此 Skill 与 fetch-reviews 不同，fetch-reviews 是获取已存在的评论，此 Skill 是触发 AI 工具进行新审查。
---

# 申请新审查工作流

## ⚠️ 与 fetch-reviews 的区别

| 操作 | Skill | 目的 |
|------|-------|------|
| **获取评论** | `fetch-reviews` | 从 GitHub 获取已存在的审查评论 |
| **申请新审查** | `request-reviews` | 触发 AI 工具进行新的审查 |

**重要**：用户说"获取评论"、"查看评论"时调用 `fetch-reviews`，用户说"申请新审查"、"重新审查"时调用此 Skill。

---

## 执行流程（强制顺序）

### 阶段 1：前置检查

**⚠️ 禁止触发新审查的情况**：

检查是否有待处理的评论：

```bash
# 检查行间评论
python tools/manage_reviews.py list --status pending --format json

# 检查总览意见
python tools/manage_reviews.py overviews --status pending
```

**执行后检查**：

- [ ] 行间评论状态已检查
- [ ] 总览意见状态已检查

| 结果 | 动作 |
|------|------|
| 有待处理的行间评论 | **停止**：报告用户，要求先通过 review-workflow 处理 |
| 有待确认的总览意见 | **停止**：报告用户，要求先通过 review-workflow 处理 |
| 全部已处理 | 输出 "✅ 阶段 1 完成"，继续阶段 2 |

输出 "✅ 阶段 1 完成"

### 阶段 2：发送审查命令

**⚠️ 必须发送两条评论！**

**执行前检查**：

- [ ] 前置检查已通过
- [ ] PR 编号已确认

**获取 PR 编号**：

优先级顺序：

1. 从 git branch 推断（如 `pr-123` → PR #123）
2. 使用 GitHub CLI 查询：`gh pr view --json number`
3. 请求用户提供 PR 编号

**发送评论**：

使用 GitHub MCP 工具发送两条评论：

```
评论1：@sourcery-ai review
评论2：/agentic_review
```

**执行后检查**：

- [ ] 两条评论已发送
- [ ] Sourcery 已触发
- [ ] Qodo 已触发

输出 "✅ 阶段 2 完成"

### 阶段 3：轮询等待

**参数**：

- 间隔：30秒
- 最大次数：10次（5分钟）
- 停止条件：检测到新评论 或 达到最大次数

**执行前检查**：

- [ ] 阶段 2 已完成
- [ ] baseline_time 已记录

**轮询逻辑**：

```
1. 记录 baseline_time = 当前时间
2. 循环（最多10次）：
   a. 等待 30 秒
   b. 调用 get_pull_request_comments 获取评论
   c. 筛选 created_at > baseline_time 且 author 是 bot 的评论
   d. 如果有新评论 → 停止轮询，返回成功
   e. 如果达到最大次数 → 告知用户，返回超时
```

**执行后检查**：

- [ ] 轮询已完成

| 结果 | 动作 |
|------|------|
| 检测到新评论 | 输出 "✅ 阶段 3 完成" |
| 超时 | 输出 "⏳ 阶段 3 完成（超时）"，建议用户稍后手动刷新 |

---

## 完整性检查（强制）

在报告完成前，必须确认：

- [ ] 阶段 1：前置检查 - 已执行
- [ ] 阶段 2：发送审查命令 - 已执行（两条评论）
- [ ] 阶段 3：轮询等待 - 已执行

**如有未执行项，流程未完成！**

---

## 输出格式

### 成功

```
✅ 新审查请求已发送
- Sourcery：已触发（@sourcery-ai review）
- Qodo：已触发（/agentic_review）
- 响应状态：检测到新评论
```

### 超时

```
⏳ 新审查请求已发送，但5分钟内未检测到响应
- Sourcery：已触发
- Qodo：已触发
- 建议：稍后手动刷新查看
```

### 前置检查失败

```
❌ 无法触发新审查

前置检查失败：
- 待处理行间评论：X 个
- 待确认总览意见：Y 个

请先通过 review-workflow 处理所有评论后再请求新审查。
```

---

## 降级策略

如果 GitHub MCP 工具失败：

1. 报告用户 MCP 工具异常
2. 提供手动操作指南：
   - 在 PR 页面手动评论 `@sourcery-ai review`
   - 在 PR 页面手动评论 `/agentic_review`
