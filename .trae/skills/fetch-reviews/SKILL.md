---
name: fetch-reviews
description: |
  获取PR的AI审查评论（内部 Skill）。
  触发：用户说"获取评论"、"查看评论"时。
  注意：此 Skill 可单独调用，也可由 review-workflow 内部调用。
---

# AI 审查获取流程

## ⚠️ 执行模式说明

### 非 Plan 模式（默认）

直接执行 CLI 命令并输出结果，不创建计划文档。

### Plan 模式（用户输入 `/plan 获取评论`）

1. 执行 CLI 命令获取评论
2. 阅读并分析所有评论内容
3. 将评论和分析写进计划文档
4. 等待用户确认后执行后续操作

---

## 执行流程（强制顺序）

### 阶段 1：获取评论数据

**执行前检查**：
- [ ] PR 编号已确认

**获取 PR 编号**：

优先级顺序：
1. 从 git branch 推断（如 `pr-123` → PR #123）
2. 使用 GitHub CLI 查询：`gh pr view --json number`
3. 请求用户提供 PR 编号

**执行**：

```bash
python tools/manage_reviews.py fetch --owner Disaster-Terminator --repo RewardsCore --pr {pr_number}
```

**执行后检查**：
- [ ] 评论数据已获取

输出 "✅ 阶段 1 完成"

### 阶段 2：阅读并分析总览意见

**⚠️ 必须阅读总览意见的内容，不能只看数量！**

**执行前检查**：
- [ ] 阶段 1 已完成

**执行**：

```bash
# 获取总览意见（JSON 格式，包含完整内容）
python tools/manage_reviews.py overviews --status pending --format json
```

**分析要求**：

1. 阅读每个总览意见的 `summary` 或 `high_level_feedback`
2. 识别总览意见中提到的关键问题
3. 如果有 `prompt_for_ai`，提取其中的 `individual_comments`
4. 将分析结果写入计划文档（Plan 模式）或输出给用户（非 Plan 模式）

**标记已读**：

阅读并分析后，使用 CLI 标记总览意见已读：

```bash
python tools/manage_reviews.py acknowledge --id {overview_id}
```

或标记所有总览意见已读：

```bash
python tools/manage_reviews.py acknowledge --all
```

**执行后检查**：
- [ ] 总览意见内容已阅读
- [ ] 总览意见已分析
- [ ] 总览意见已标记已读（acknowledge）

输出 "✅ 阶段 2 完成"

### 阶段 3：阅读并分析行级评论

**⚠️ 必须阅读每个评论的内容，不能只看数量！**

**执行前检查**：
- [ ] 阶段 2 已完成

**执行**：

```bash
# 获取行级评论（JSON 格式，包含完整内容）
python tools/manage_reviews.py list --status pending --format json
```

**分析要求**：

1. 阅读每个评论的 `primary_comment_body`
2. 如果有 `enriched_context`，提取 `issue_type` 和 `issue_to_address`
3. 按分类整理评论：
   - 🔴 必须修复：Bug/Security 等
   - 🟡 自主决断：suggestion 等
4. 对每个评论给出处理建议
5. 将分析结果写入计划文档（Plan 模式）或输出给用户（非 Plan 模式）

**执行后检查**：
- [ ] 每个评论内容已阅读
- [ ] 每个评论已分类
- [ ] 每个评论有处理建议

输出 "✅ 阶段 3 完成"

---

## 完整性检查（强制）

在报告完成前，必须确认：
- [ ] 阶段 1：获取评论数据 - 已执行
- [ ] 阶段 2：阅读并分析总览意见 - 已执行（内容已阅读、已分析、已标记已读）
- [ ] 阶段 3：阅读并分析行级评论 - 已执行（每个评论已阅读、已分类、有处理建议）

**如有未执行项，流程未完成！**

---

## 输出格式

### Plan 模式输出格式

计划文档应包含以下内容：

```markdown
# PR 审查评论分析报告

## 一、总览意见（X 条）

### 总览意见 1
- **来源**：Sourcery/Qodo
- **内容**：{summary 或 high_level_feedback}
- **关键问题**：{Agent 分析}
- **处理建议**：{Agent 建议}

## 二、行级评论（Y 条）

### 🔴 必须修复（X 条）

| ID | 来源 | 类型 | 位置 | 问题 | 处理建议 |
|----|------|------|------|------|----------|
| ... | ... | ... | file:line | ... | ... |

### 🟡 自主决断（Y 条）

| ID | 来源 | 类型 | 位置 | 问题 | 处理建议 |
|----|------|------|------|------|----------|
| ... | ... | ... | file:line | ... | ... |

## 三、后续操作建议

1. {建议 1}
2. {建议 2}

---
请确认是否执行上述处理建议。
```

### 非 Plan 模式输出格式

#### 成功

```
✅ 评论获取完成

### 总览意见（X 条）
| ID | 来源 | 状态 | 摘要 |
|----|------|------|------|
| ... | Sourcery/Qodo | pending | ... |

### 行级评论（Y 条）
| 分类 | 数量 | 说明 |
|------|------|------|
| 🔴 必须修复 | X 条 | Bug/Security 等 |
| 🟡 自主决断 | Y 条 | suggestion 等 |

### 详细列表
（CLI 表格输出）
```

#### 无评论

```
✅ 评论获取完成
- 总览意见：0 条
- 行级评论：0 条
- PR 无待处理评论
```

---

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

---

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

---

## 降级策略

如果 CLI 工具失败，参考 `docs/reference/archive/v1-ai-reviewer-guide.md` 使用 Playwright 手动获取评论。

该文档包含三种机器人的审查评论格式和规律：
- Sourcery: `sourcery-ai bot`
- Copilot: `Copilot AI`
- Qodo: `qodo-code-review bot`

---

## 严禁事项

- **严禁只看数量不看内容**：必须阅读每个评论的内容
- **严禁跳过总览意见标记**：必须用 CLI acknowledge 标记已读
- **严禁一次性解决所有评论**：每个评论必须单独处理
- **严禁无依据标记解决**：必须先确认问题已解决
- **严禁批量操作**：必须逐个评论处理
- **严禁跳过说明评论**：rejected/false_positive 必须回复
- **Agent 不自动合并 PR**：需通知用户确认
