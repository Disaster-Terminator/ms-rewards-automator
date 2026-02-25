---
name: review-workflow
description: |
  PR 审查评论处理工作流（强制闭环）。
  触发：用户说"处理评论"、"解决评论"、"PR 评论"时。
  ⚠️ 必须完整执行所有阶段，不可跳过！
---

# PR 审查评论处理工作流

## ⚠️ 强制闭环声明

此工作流必须完整执行到"解决评论"阶段：
1. 仅修改代码不算完成
2. 修复后必须调用 acceptance-workflow 验收
3. 验收通过后必须调用 CLI 解决评论
4. 最后必须确认总览评论

---

## 执行流程（强制顺序）

### 阶段 1：获取 PR 编号与评论

**Step 1: 获取 PR 编号**

优先级顺序：
1. 从 git branch 推断（如 `pr-123` → PR #123）
2. 使用 GitHub CLI 查询：`gh pr view --json number`
3. 请求用户提供 PR 编号

**Step 2: 获取评论**

- [ ] PR 编号已确认

```bash
python tools/manage_reviews.py fetch --owner Disaster-Terminator --repo RewardsCore --pr {pr_number}
python tools/manage_reviews.py list --status pending --format json
python tools/manage_reviews.py overviews --status pending
```

**执行后检查**：
- [ ] 评论列表已获取
- [ ] 总览意见已获取

输出 "✅ 阶段 1 完成"

### 阶段 2：分类评估

**必须修复（红色）**：

| 来源 | issue_type | 行为 |
|------|------------|------|
| Sourcery | bug_risk, security | 必须修复 |
| Qodo | Bug, Security, Rule violation, Reliability | 必须修复 |

**自主决断（黄色）**：

| 来源 | issue_type | 决策原则 |
|------|------------|----------|
| Sourcery | suggestion, performance | 评估是否真正改进代码质量 |
| Qodo | Correctness | 评估是否真正提高正确性 |
| Copilot | suggestion | 评估是否适用当前场景 |

**执行后检查**：
- [ ] 分类完成
- [ ] 必须修复项已识别

输出 "✅ 阶段 2 完成"

### 阶段 3：修复代码

**执行前检查**：
- [ ] 分类评估已完成
- [ ] 必须修复项已处理或已报告用户

修改代码后，继续阶段 4。

**执行后检查**：
- [ ] 代码已修改
- [ ] 修改已保存

输出 "✅ 阶段 3 完成"

### 阶段 4：验收（强制调用）

**⚠️ 此阶段不可跳过！修复后必须验收！**

**熔断机制**：连续 2 次验收失败后，停止执行并等待人类干预。

**执行前检查**：
- [ ] 阶段 1-3 已完成
- [ ] 代码已修改

**执行**：
调用 acceptance-workflow Skill 执行完整验收流程。

**执行后检查**：
- [ ] acceptance-workflow 已调用
- [ ] 验收结果已获取

| 结果 | 动作 |
|------|------|
| 验收通过 | 输出 "✅ 阶段 4 完成"，继续阶段 5 |
| 验收失败（首次） | 分析错误，修复代码，重新执行 acceptance-workflow |
| 验收失败（连续第 2 次） | **触发熔断**：停止执行，输出错误汇总及诊断，等待人类干预 |

### 阶段 5：解决评论（强制执行）

**⚠️ 此阶段不可跳过！验收通过后必须解决评论！**

**执行前检查**：
- [ ] 验收已通过
- [ ] 评论列表已获取

**执行**：

修复代码：
```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type code_fixed
```

拒绝建议：
```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type rejected --reply "拒绝理由：{具体原因}"
```

误报：
```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type false_positive --reply "误报说明：{具体原因}"
```

**执行后检查**：
- [ ] 每个已修复的评论都调用了 `resolve --type code_fixed`
- [ ] 每个拒绝的建议都调用了 `resolve --type rejected --reply "..."`
- [ ] 每个误报都调用了 `resolve --type false_positive --reply "..."`

输出 "✅ 阶段 5 完成"

### 阶段 6：确认总览评论

**⚠️ 总览评论必须确认！**

**执行前检查**：
- [ ] 阶段 5 已完成

**执行**：
```bash
python tools/manage_reviews.py acknowledge --all
```

**执行后检查**：
- [ ] 总览意见已确认

输出 "✅ 阶段 6 完成"

---

## 完整性检查（强制）

在报告完成前，必须确认：
- [ ] 阶段 1：获取评论 - 已执行
- [ ] 阶段 2：分类评估 - 已执行
- [ ] 阶段 3：修复代码 - 已执行
- [ ] 阶段 4：验收 - 已执行（调用了 acceptance-workflow）
- [ ] 阶段 5：解决评论 - 已执行（CLI 命令已调用）
- [ ] 阶段 6：确认总览 - 已执行

**如有未执行项，流程未完成！**

---

## 失败恢复

如果工作流中断，检查已完成项并从断点继续：

| 中断点 | 恢复方式 |
|--------|----------|
| 阶段 1-2 | 重新执行 review-workflow |
| 阶段 3 | 检查代码修改状态，继续阶段 4 |
| 阶段 4 | 重新执行 acceptance-workflow |
| 阶段 5-6 | 检查评论状态，继续解决 |

**快速跳过已完成项**：
- 评论已解决 → 跳过
- 测试已通过 → 跳过

---

## 降级策略

如果 CLI 工具失败：
1. 报告用户 CLI 工具异常
2. 提供手动操作指南（参考 docs/reference/archive/ai-reviewer-guide.md）

---

## 输出格式

### 成功

```
✅ 审查评论处理完成
- 已修复：X 个
- 已拒绝：Y 个（附理由）
- 误报：Z 个（附说明）
- 验收：通过
- 总览意见：已确认

### 评论处理结果
| ID | 来源 | 类型 | 处理方式 | CLI 命令 | 状态 |
|----|------|------|----------|----------|------|
| #1 | Sourcery | bug_risk | code_fixed | resolve --thread-id xxx --type code_fixed | ✅ |
```

### 失败（未闭环）

```
❌ 审查评论处理未完成
- 阶段 4 验收：未执行
- 阶段 5 解决评论：未执行
- 阶段 6 确认总览：未执行
- 请继续执行未完成的阶段
```

### 熔断触发

```
⚠️ 验收熔断触发
- 连续失败次数：2
- 错误汇总：
  1. <第一次错误>
  2. <第二次错误>
- 初步诊断：<诊断结果>
- 请人类干预处理
```
