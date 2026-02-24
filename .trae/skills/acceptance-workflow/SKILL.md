---
name: acceptance-workflow
description: |
  完整验收工作流（阶段1-5）。
  自动执行：静态检查 → 单元测试 → 集成测试 → 审查评论检查 → E2E无头验收。
  任何阶段失败都会停止并报告。
---

# 完整验收工作流

## 执行流程（强制顺序）

### 阶段 1：静态检查

```bash
ruff check . && ruff format --check .
```

| 结果 | 动作 |
|------|------|
| 通过 | 继续阶段 2 |
| 失败 | 停止，报告错误 |

### 阶段 2：单元测试（并行）

```bash
pytest tests/unit/ -n auto -v --tb=short --timeout=60 -m "not real"
```

| 结果 | 动作 |
|------|------|
| 全部通过 | 继续阶段 3 |
| 有失败 | 停止，报告错误 |

### 阶段 3：集成测试（并行）

```bash
pytest tests/integration/ -n auto -v --tb=short --timeout=120
```

| 结果 | 动作 |
|------|------|
| 全部通过 | 继续阶段 3.5 |
| 有失败 | 停止，报告错误 |

### 阶段 3.5：审查评论检查（如有PR）

**前置条件**：当前有活跃的PR

#### Step 1: 获取评论状态

```bash
python tools/manage_reviews.py list --status pending --format json
```

解析输出，获取每个 Thread 的 `enriched_context`。

#### Step 2: 分类处理

**必须修复项判断**：

检查 `enriched_context.issue_type`，如果包含以下类型，标记为必须修复：

| 类型 | 来源 |
|------|------|
| Bug, Security, Rule violation, Reliability | Qodo |
| bug_risk, security | Sourcery |

```python
MUST_FIX_TYPES = {"Bug", "Security", "Rule violation", "Reliability", "bug_risk", "security"}

def is_must_fix(issue_type: str) -> bool:
    for type_name in MUST_FIX_TYPES:
        if type_name.lower() in issue_type.lower():
            return True
    return False
```

**处理逻辑**：

| 分类 | 行为 |
|------|------|
| 有必须修复项 | 停止验收，报告用户 |
| 仅有自主决断项 | Agent 可自主决定是否采纳 |

**自主决断项类型**：

| 类型 | 来源 |
|------|------|
| suggestion | Sourcery |
| Correctness, performance | Qodo |

#### Step 3: 自动解决已修复项

对于已修复的评论：

```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type code_fixed
```

对于拒绝的建议：

```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type rejected --reply "拒绝原因"
```

#### Step 4: 确认总览意见

```bash
python tools/manage_reviews.py acknowledge --all
```

#### 输出格式

**成功**：

```
✅ 审查评论检查通过
- 必须修复：0 待处理
- 建议性：X 已忽略，0 待判断
- 已解决：Y
- 总览意见：已确认
```

**失败**：

```
❌ 审查评论检查失败
- 必须修复：X 待处理
  - Thread ID: xxx (Bug)
  - Thread ID: yyy (Security)
- 请先处理上述问题
```

**解决结果统计**：

```
### 评论解决结果
| ID | 来源 | 类型 | 解决依据 | 回复 | 状态 |
|----|------|------|----------|------|------|
| #1 | Sourcery | bug_risk | code_fixed | - | ✅ |
| #2 | Copilot | suggestion | rejected | 已说明 | ✅ |
```

**注意**：如果没有活跃PR，跳过此阶段。

### 阶段 4-5：E2E 无头验收

调用 e2e-acceptance skill 执行。

---

## 输出格式

### 全部通过

```
✅ 验收工作流完成
- 静态检查：通过
- 单元测试：X passed（并行执行）
- 集成测试：Y passed（并行执行）
- 审查评论：通过（如有PR）
- Dev 无头验收：通过
- User 无头验收：通过
```

### 阶段 N 失败

```
❌ 验收工作流在阶段 N 失败

### 错误详情
<错误信息>
```

---

## 流程图

```
阶段1: 静态检查
       ↓
阶段2: 单元测试
       ↓
阶段3: 集成测试
       ↓
阶段3.5: 审查评论检查（如有PR）
       │
       ├─ Step 1: 获取评论状态
       │
       ├─ Step 2: 分类处理
       │   ├─ 必须修复项 → 停止，报告用户
       │   └─ 自主决断项 → Agent 决定是否采纳
       │
       ├─ Step 3: 自动解决已修复项
       │
       └─ Step 4: 确认总览意见
       ↓
   ┌───┴───┐
   ↓       ↓
  通过    失败
   ↓       ↓
阶段4-5  停止报告
E2E验收
   ↓
  完成
```

## 相关 Skills

- [fetch-reviews](../fetch-reviews/SKILL.md) - 获取评论
- [resolve-review-comment](../resolve-review-comment/SKILL.md) - 解决评论
- [e2e-acceptance](../e2e-acceptance/SKILL.md) - E2E 无头验收
