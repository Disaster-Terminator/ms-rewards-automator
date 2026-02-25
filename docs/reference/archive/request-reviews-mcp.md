# v1 请求AI审查流程 (MCP 版本)

> **归档说明**：此文档为 v1 版本，使用 GitHub MCP。已归档。
> 正常情况下请使用 v2 CLI 工具。如果 CLI 失败，可参考此文档作为降级方案。

## Qodo v1 vs v2 背景

> **重要区分**：Qodo v1/v2 与项目架构 v1/v2 是不同概念。

### Qodo v1 (PR Review) - 已归档

- 斜杠命令：`/review`
- 产物：Issue Comment (PR Review)
- 本文档描述的流程

### Qodo v2 (Code Review) - 当前使用

- 斜杠命令：`/agentic_review`
- 产物：Issue Comment (Code Review)
- 项目创建时自动执行
- 更新行为：在原 Issue Comment 添加更新说明 + 新增逐行评论

## 前置条件检查

**重要**：触发新审查前必须满足以下条件：

```
1. 调用 fetch-reviews 获取当前评论状态
2. 确认没有"待处理"状态的必须修复项
3. 确认所有建议性评论都有明确状态（已忽略/已解决）
4. 如果有未处理项 → 停止，先处理
```

**禁止触发新审查的情况**：

- 有未解决的必须修复评论
- 有未判断的建议性评论
- 用户未明确要求新审查

## 触发条件

- 用户明确请求"新审查"或"重新审查"
- 修复了必须修复项后需要验证
- **不**因推送代码而自动触发

## 执行流程

### 步骤 1：前置检查

```
1. 获取当前评论状态
2. 输出推送检查结果
3. 如果检查失败 → 停止，报告用户
4. 如果检查通过 → 继续步骤2
```

### 步骤 2：发送审查命令

**重要**：评论必须只包含命令，不能有多余内容。

**Qodo v1 (PR Review)**：

```
# 评论1：触发 Sourcery
add_issue_comment(owner, repo, issue_number, body="@sourcery-ai review")

# 评论2：触发 Qodo v1
add_issue_comment(owner, repo, issue_number, body="/review")
```

**Qodo v2 (Code Review)**：

```
# 评论1：触发 Sourcery
add_issue_comment(owner, repo, issue_number, body="@sourcery-ai review")

# 评论2：触发 Qodo v2
add_issue_comment(owner, repo, issue_number, body="/agentic_review")
```

### 步骤 3：轮询等待响应

**参数**：

- 间隔：30秒
- 最大次数：10次（5分钟）
- 停止条件：检测到新评论 或 达到最大次数

**逻辑**：

```
1. 记录 baseline_time = 当前时间
2. 循环：
   a. 等待 30 秒
   b. 调用 get_pull_request_comments 获取评论
   c. 筛选 created_at > baseline_time 且 author 是 bot 的评论
   d. 如果有新评论 → 停止轮询，返回成功
   e. 如果达到最大次数 → 告知用户，返回超时
```

## 输出格式

### 前置检查失败

```
❌ 无法触发新审查

推送检查失败：
- 必须修复：2 待处理
- 建议性：1 待判断

请先处理上述问题后再请求新审查。
```

### 成功

```
✅ 审查请求已发送，检测到新评论响应
```

### 超时

```
⏳ 审查请求已发送，但5分钟内未检测到响应
建议：稍后手动刷新查看
```

## 流程图

```
用户请求新审查
       ↓
  前置条件检查
       ↓
   ┌───┴───┐
   ↓       ↓
  失败     通过
   ↓       ↓
报告用户  发送审查命令
          ↓
       轮询等待
          ↓
      ┌───┴───┐
      ↓       ↓
    成功     超时
      ↓       ↓
    完成    报告用户
```
