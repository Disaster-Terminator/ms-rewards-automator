---
name: fetch-reviews
description: |
  拉取并处理 PR 审查评论（核心 Skill）。
  触发：用户说"获取审查"、"查看评论"时。
  注意：此 Skill 可单独调用，也可由 request-reviews 内部调用。
---

# 拉取并处理评论

## ⚠️ 执行声明

**拉取评论是只读操作，不需要用户确认，无论是否在 Plan 模式！**

| 模式 | 行为 |
|------|------|
| 非 Plan 模式 | 阶段 1 → 2 → 3 → 4 → 输出报告 |
| Plan 模式 | 阶段 1 → 2 → 3 → 写入计划文档 |

---

## CLI 命令速查

### 拉取和查看

```bash
# 拉取评论到本地
python tools/manage_reviews.py fetch --owner Disaster-Terminator --repo RewardsCore --pr {pr_number}

# 查看本地评论（fetch 后执行）
python tools/manage_reviews.py list --status pending --format json

# 查看总览意见
python tools/manage_reviews.py overviews --format json
```

### 解决行级评论

```bash
# 修复代码后
python tools/manage_reviews.py resolve --owner Disaster-Terminator --repo RewardsCore --thread-id {thread_id} --type code_fixed

# 采纳建议
python tools/manage_reviews.py resolve --owner Disaster-Terminator --repo RewardsCore --thread-id {thread_id} --type adopted

# 拒绝建议
python tools/manage_reviews.py resolve --owner Disaster-Terminator --repo RewardsCore --thread-id {thread_id} --type rejected --reply "拒绝理由"

# 误报
python tools/manage_reviews.py resolve --owner Disaster-Terminator --repo RewardsCore --thread-id {thread_id} --type false_positive --reply "误报说明"

# 已过时
python tools/manage_reviews.py resolve --owner Disaster-Terminator --repo RewardsCore --thread-id {thread_id} --type outdated
```

### 确认总览意见

```bash
# 确认单条
python tools/manage_reviews.py acknowledge --id {overview_id}

# 确认全部
python tools/manage_reviews.py acknowledge --all
```

---

## 执行流程

### 阶段 1：拉取评论

**工具**：RunCommand

**命令**：

```bash
python tools/manage_reviews.py fetch --owner Disaster-Terminator --repo RewardsCore --pr {pr_number}
```

**输出**：评论已保存到本地

**下一步**：阶段 2

---

### 阶段 2：查看评论

**工具**：RunCommand

**命令**：

```bash
python tools/manage_reviews.py list --status pending --format json
python tools/manage_reviews.py overviews --format json
```

**输出**：JSON 格式的评论列表

**关键字段**：

| 字段 | 含义 | 用途 |
|------|------|------|
| `thread_id` | 线程 ID | resolve 命令参数 |
| `source` | 来源 | Sourcery/Qodo/Copilot |
| `file_path` | 文件路径 | Read 命令参数 |
| `line_number` | 行号 | 定位代码 |
| `primary_comment_body` | 评论内容 | 分析问题 |
| `issue_type` | 问题类型 | 裁决优先级 |

**下一步**：对每个评论执行阶段 3

---

### 阶段 3：分析评论

**输入**：单条评论数据（从阶段 2 的 JSON 中提取）

**步骤**：

#### 3.1 提取信息

从评论数据中提取：

- `file_path` → 文件路径
- `line_number` → 行号
- `primary_comment_body` → 评论内容
- `issue_type` → 问题类型

#### 3.2 读取代码

**工具**：Read

**参数**：

```
file_path: {file_path}
offset: max(1, line_number - 10)
limit: 20
```

**目的**：获取评论指向的代码上下文

#### 3.3 对比分析

回答以下问题：

1. 评论说的问题是什么？
2. 当前代码是什么样的？
3. 问题是否存在？

**输出表格**：

| 字段 | 值 |
|------|-----|
| thread_id | {从数据提取} |
| 位置 | {file_path}:{line_number} |
| 评论内容 | {primary_comment_body} |
| 当前代码 | ```代码片段``` |
| 问题是否存在 | 是/否/部分 |
| 建议处理 | code_fixed/adopted/rejected/false_positive/outdated |

**下一步**：

- Plan 模式 → 写入计划文档
- 非 Plan 模式 → 阶段 4

---

### 阶段 4：执行处理

**根据阶段 3 的分析结果**：

| 分析结果 | 处理方式 | CLI 命令 |
|----------|----------|----------|
| 问题存在 | 修复代码 → 验证 → resolve | `--type code_fixed` |
| 采纳建议 | 修改代码 → 验证 → resolve | `--type adopted` |
| 拒绝建议 | 说明理由 → resolve | `--type rejected --reply "理由"` |
| 误报 | 说明原因 → resolve | `--type false_positive --reply "原因"` |
| 已过时 | resolve | `--type outdated` |

**工具**：

- 修复代码：SearchReplace
- CLI 标记：RunCommand

---

## 完整性检查

### Plan 模式

- [ ] 阶段 1：拉取评论 - 已执行
- [ ] 阶段 2：查看评论 - 已执行
- [ ] 阶段 3：分析评论 - 已执行（每个评论已读取代码、对比分析）
- [ ] 写入计划文档 - 已执行

### 非 Plan 模式

- [ ] 阶段 1：拉取评论 - 已执行
- [ ] 阶段 2：查看评论 - 已执行
- [ ] 阶段 3：分析评论 - 已执行
- [ ] 阶段 4：执行处理 - 已执行（代码已修复、CLI 已标记）
- [ ] 输出报告 - 已执行

---

## 输出格式

### Plan 模式

写入 `.trae/plans/fetch-reviews-plan.md`：

```markdown
# PR 审查评论处理计划

## 评论列表

| ID | 来源 | 位置 | 问题 | 建议处理 |
|----|------|------|------|----------|
| xxx | Sourcery | file:123 | 问题描述 | code_fixed |

## 详细分析

### 评论 1
- **位置**：file:line
- **评论内容**：{primary_comment_body}
- **当前代码**：
  ```

  {代码片段}

  ```
- **问题是否存在**：是/否/部分
- **建议处理**：{处理方式}
- **理由**：{分析理由}

---
请确认后执行处理。
```

### 非 Plan 模式

```markdown
# PR 审查评论处理报告

## 处理结果

| ID | 来源 | 位置 | 问题 | 处理方式 | CLI 命令 |
|----|------|------|------|----------|----------|
| xxx | Sourcery | file:123 | 问题描述 | code_fixed | resolve ... |

## 详细说明

### 评论 1
- **问题**：{描述}
- **代码**：{代码片段}
- **分析**：{Agent 分析}
- **处理**：{修复代码或说明}
- **验证**：{结果}

---
请确认处理结果。
```

### 无评论

```markdown
✅ GitHub 无新评论

是否要申请新的 AI 审查？
- 输入"是"或"申请新审查"触发 request-reviews
- 输入"否"结束
```

---

## 业务裁决规则

### 必须修复

| 来源 | issue_type |
|------|------------|
| Sourcery | `bug_risk`, `security` |
| Qodo | `Bug`, `Security`, `Rule violation`, `Reliability` |

**行为**：修复代码

### 自主决断

| 来源 | issue_type |
|------|------------|
| Sourcery | `suggestion`, `performance` |
| Qodo | `Correctness` |

**行为**：分析利弊，给出建议

---

## 降级策略

如果 CLI 工具失败，参考 `docs/reference/archive/ai-reviewer-guide.md` 使用 Playwright 手动获取评论。

---

## 严禁事项

- **严禁不读取代码就分析**：必须用 Read 工具读取文件
- **严禁跳过代码对比**：必须对比评论内容和当前代码
- **严禁跳过 CLI 标记**：必须标记评论状态
