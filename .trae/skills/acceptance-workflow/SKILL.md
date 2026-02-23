---
name: acceptance-workflow
description: |
  完整验收工作流（阶段1-5）。
  自动执行：静态检查 → 单元测试 → 集成测试 → Dev无头验收 → User无头验收。
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
| 全部通过 | 继续阶段 4 |
| 有失败 | 停止，报告错误 |

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
- Dev 无头验收：通过
- User 无头验收：通过
```

### 阶段 N 失败

```
❌ 验收工作流在阶段 N 失败

### 错误详情
<错误信息>
```
