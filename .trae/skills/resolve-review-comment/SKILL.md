---
name: resolve-review-comment
description: |
  解决PR审查评论（内部 Skill）。
  触发：用户说"解决某个评论"时。
  注意：此 Skill 可单独调用，也可由 review-workflow 内部调用。
---

# 解决审查评论

## 问题类型判断

### 必须修复（红色）

以下问题类型必须修复，Agent 应报告用户等待修复指令：

| 类型 | 来源 |
|------|------|
| Bug | Qodo |
| Security | Qodo |
| Rule violation | Qodo |
| Reliability | Qodo |
| bug_risk | Sourcery |
| security | Sourcery |

**Agent 行为**：报告用户，等待修复指令

### 自主决断（黄色）

以下问题类型可由 Agent 自主决定是否采纳：

| 类型 | 来源 |
|------|------|
| suggestion | Sourcery |
| Correctness | Qodo |
| performance | Sourcery/Qodo |

**Agent 行为**：报告用户，自主决断是否采纳

## enriched_context 使用

### 获取问题信息

```bash
python tools/manage_reviews.py list --status pending --format json
```

### 解析 enriched_context

| 字段 | 说明 | 来源 |
|------|------|------|
| `issue_type` | 问题类型 | Qodo Emoji 或 Sourcery Prompt |
| `issue_to_address` | 问题描述 | Sourcery Prompt |
| `code_context` | 代码上下文 | Sourcery Prompt |

### 判断问题类型

```python
MUST_FIX_TYPES = {"Bug", "Security", "Rule violation", "Reliability", "bug_risk", "security"}

def is_must_fix(issue_type: str) -> bool:
    for type_name in MUST_FIX_TYPES:
        if type_name.lower() in issue_type.lower():
            return True
    return False
```

## 执行命令

### 解决评论线程

```bash
python tools/manage_reviews.py resolve --thread-id {thread_id} --type {resolution_type} [--reply "{reply_content}"]
```

### 确认总览意见

```bash
# 确认单个总览意见
python tools/manage_reviews.py acknowledge --id {overview_id}

# 确认所有总览意见
python tools/manage_reviews.py acknowledge --all
```

## 参数说明

### resolve 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--thread-id` | 是 | Thread ID（从 fetch-reviews 获取） |
| `--type` | 是 | 解决类型 |
| `--reply` | 条件 | rejected/false_positive 时必需 |

### acknowledge 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--id` | 二选一 | 总览意见 ID |
| `--all` | 二选一 | 确认所有总览意见 |

## 解决类型

| 类型 | 含义 | 需要回复 |
|------|------|----------|
| `code_fixed` | 代码已修复 | 否 |
| `adopted` | 已采纳建议 | 否 |
| `rejected` | 拒绝建议 | **是** |
| `false_positive` | 误报 | **是** |
| `outdated` | 已过时 | 否 |

## 使用示例

### 代码已修复

```bash
python tools/manage_reviews.py resolve --thread-id "MDI0OlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkMTIz" --type code_fixed
```

### 拒绝建议（需回复）

```bash
python tools/manage_reviews.py resolve --thread-id "MDI0OlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNDU2" --type rejected --reply "此建议不适用于当前场景，因为该代码路径在异步上下文中运行。"
```

### 误报（需回复）

```bash
python tools/manage_reviews.py resolve --thread-id "MDI0OlB1bGxSZXF1ZXN0UmV2aWV3VGhyZWFkNzg5" --type false_positive --reply "此警告为误报，变量在使用前已通过类型守卫确保非空。"
```

### 确认总览意见

```bash
# 确认所有总览意见
python tools/manage_reviews.py acknowledge --all

# 确认单个总览意见
python tools/manage_reviews.py acknowledge --id "IC_kwDO..."
```

## JSON 输出

### resolve 成功

```json
{
    "success": true,
    "message": "线程 {thread_id} 已解决",
    "resolution_type": "code_fixed",
    "reply_posted": false
}
```

### acknowledge 成功

```json
{
    "success": true,
    "message": "已确认 X 个总览意见",
    "acknowledged_ids": ["id1", "id2"]
}
```

## 严禁事项

| 禁止行为 | 原因 |
|----------|------|
| 无依据标记解决 | 必须先修复代码或有合理理由 |
| 跳过说明评论 | rejected/false_positive 必须回复说明原因 |
| 猜测 Thread ID | 必须使用 fetch-reviews 获取的 Thread ID |
| 忽略必须修复项 | Bug/Security 类型必须报告用户 |
| 跳过总览意见确认 | 总览意见应确认已阅读 |

## 降级策略

如果 CLI 工具失败，参考 `docs/reference/archive/ai-reviewer-guide.md`。
