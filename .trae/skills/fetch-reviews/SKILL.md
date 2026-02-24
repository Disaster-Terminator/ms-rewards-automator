---
name: fetch-reviews
description: |
  获取PR的AI审查评论（内部 Skill）。
  触发：用户说"获取评论"、"查看评论"时。
  注意：此 Skill 可单独调用，也可由 review-workflow 内部调用。
---

# AI 审查获取流程

## 核心概念

### 操作对象 vs 参考对象

| 类型 | 模型 | 用途 | 操作 |
|------|------|------|------|
| **Thread** | `ReviewThreadState` | 主要操作对象 | 可解决、可回复 |
| **Overview** | `ReviewOverview` | 总览意见（Sourcery/Qodo） | 需通过 CLI acknowledge |
| **IssueCommentOverview** | `IssueCommentOverview` | 只读参考 | 仅阅读，不可解决 |

**重要**：

- Thread 是行级评论，主要操作对象
- Overview 是总览意见，Sourcery/Qodo 会给出高层建议
- **Overview 必须通过 CLI `acknowledge` 命令处理，不能忽略**

## 执行命令

```bash
python tools/manage_reviews.py fetch --owner {owner} --repo {repo} --pr {pr_number}
```

## 完整工作流程

### 步骤 1：获取评论数据

```bash
python tools/manage_reviews.py fetch --owner {owner} --repo {repo} --pr {pr_number}
```

### 步骤 2：查看总览意见（Overview）

```bash
# 查看所有总览意见
python tools/manage_reviews.py overviews

# 仅查看待处理的
python tools/manage_reviews.py overviews --status pending
```

**重要**：

- 总览意见给出 PR 整体评价
- `prompt_for_ai.individual_comments` 包含行级建议（如果有）
- 必须使用 `acknowledge` 命令标记处理状态

### 步骤 3：处理总览意见

```bash
# 确认单个总览意见
python tools/manage_reviews.py acknowledge --id {overview_id}

# 确认所有总览意见
python tools/manage_reviews.py acknowledge --all
```

### 步骤 4：处理行级评论（Thread）

```bash
# 列出待处理的行级评论
python tools/manage_reviews.py list --status pending
```

然后逐个处理 Thread，使用 `resolve-review-comment` Skill。

## Thread 数据结构

### 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | Thread ID（用于解决操作） |
| `source` | string | 评论来源：`Sourcery` / `Qodo` / `Copilot` |
| `local_status` | string | 本地状态：`pending` / `resolved` / `ignored` |
| `is_resolved` | boolean | GitHub 上的解决状态 |
| `file_path` | string | 文件路径 |
| `line_number` | number | 行号 |
| `primary_comment_body` | string | 评论内容 |
| `enriched_context` | object | 结构化元数据（可选） |

### enriched_context 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `issue_type` | string | 问题类型（如 "Bug", "Security", "suggestion"） |
| `issue_to_address` | string | 问题描述（来自 Sourcery Prompt） |
| `code_context` | string | 代码上下文（来自 Sourcery Prompt） |

### 处理逻辑

```
只处理 local_status == "pending" 且 is_resolved == False 的线程
```

## 业务裁决规则

### 必须修复（红色）

| 来源 | issue_type |
|------|------------|
| Sourcery | `bug_risk`, `security` |
| Qodo | `Bug`, `Security`, `Rule violation`, `Reliability` |
| Copilot | 安全警告 |

**行为**：报告给用户，等待修复指令

### 自主决断（黄色）

| 来源 | issue_type |
|------|------------|
| Sourcery | `suggestion`, `performance` |
| Qodo | `Correctness` |
| Copilot | `suggestion` 代码块 |

**行为**：报告给用户，自主决断是否采纳

## CLI 命令

### 获取评论

```bash
python tools/manage_reviews.py fetch --owner {owner} --repo {repo} --pr {pr_number}
```

### 列出线程（表格格式）

```bash
# 默认表格输出
python tools/manage_reviews.py list --status pending

# JSON 输出
python tools/manage_reviews.py list --status pending --format json
```

### 查看总览意见

```bash
python tools/manage_reviews.py overviews
```

### 处理总览意见（acknowledge）

**重要**：Overview 是 Sourcery/Qodo 给出的总览意见，必须通过 CLI 处理。

```bash
# 查看待处理的总览意见
python tools/manage_reviews.py overviews --status pending

# 确认单个总览意见
python tools/manage_reviews.py acknowledge --id {overview_id}

# 确认所有总览意见
python tools/manage_reviews.py acknowledge --all
```

**Overview 数据结构**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | Overview ID |
| `source` | string | 来源：`Sourcery` / `Qodo` |
| `summary` | string | 总览内容 |
| `prompt_for_ai` | object | AI 处理提示（可选） |
| `local_status` | string | 本地状态：`pending` / `acknowledged` / `ignored` |

**处理流程**：

1. 使用 `overviews` 命令查看总览意见
2. 阅读总览内容，理解 PR 整体评价
3. 使用 `acknowledge` 命令标记处理状态
4. 如果 `prompt_for_ai` 存在，其中包含 `individual_comments`，这些是行级建议

### 查看统计

```bash
python tools/manage_reviews.py stats
```

## 输出格式

### 表格输出示例

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       待处理评论 (5)                                      │
├──────────────┬──────────┬──────────┬────────────┬──────────────────────┤
│ ID           │ Source   │ Status   │ Enriched   │ Location             │
├──────────────┼──────────┼──────────┼────────────┼──────────────────────┤
│ PRRT_kwDO... │ Qodo     │ pending  │ ✅ Bug     │ requirements.txt:1   │  ← 红色（必须修复）
│ PRRT_kwDO... │ Sourcery │ pending  │ ✅ Sec     │ cli.py:42           │  ← 红色（必须修复）
│ PRRT_kwDO... │ Copilot  │ pending  │            │ utils.py:15         │
│ PRRT_kwDO... │ Qodo     │ pending  │ ✅ Cor     │ config.py:10        │  ← 黄色（建议）
└──────────────┴──────────┴──────────┴────────────┴──────────────────────┘
```

### 颜色说明

- **红色行**：必须修复的问题（Bug、Security 等）
- **黄色行**：建议性问题（Correctness、suggestion 等）
- **✅**：已注入 enriched_context

## 降级策略

如果 CLI 工具失败，参考 `docs/reference/archive/v1-ai-reviewer-guide.md` 使用 Playwright 手动获取评论。

该文档包含三种机器人的审查评论格式和规律：

- Sourcery: `sourcery-ai bot`
- Copilot: `Copilot AI`
- Qodo: `qodo-code-review bot`

## 严禁事项

- **严禁一次性解决所有评论**：每个评论必须单独处理
- **严禁无依据标记解决**：必须先确认问题已解决
- **严禁批量操作**：必须逐个评论处理
- **严禁跳过说明评论**：rejected/false_positive 必须回复
- **Agent 不自动合并 PR**：需通知用户确认
