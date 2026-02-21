---
name: mcp-acceptance
description: 执行 MCP 驱动的 7 阶段验收流程。当代码修改完成需要验收时触发，或用户请求运行验收。
---

# MCP 验收流程

## 触发条件

- 代码修改完成，需要验收
- 用户请求运行验收流程

## 阶段概览

```text
阶段 1-3: CI 自动化（静态检查 → 单元测试 → 集成测试）
阶段 4-5: MCP 无头验收（Dev无头 → User无头）
阶段 6-7: PR 管理（创建PR → 等待审查 → 合并确认）
```

## 阶段 1-3：CI 自动化

```bash
# 阶段 1：静态检查
ruff check . && ruff format --check .

# 阶段 2：单元测试
pytest tests/unit/ -m "not real" -v

# 阶段 3：集成测试
pytest tests/integration/ -v
```

## 阶段 4：Dev 无头验证

**执行命令**：

```bash
# 优先使用 conda 环境解释器
D:\miniconda3\envs\{env_name}\python.exe main.py --dev --headless

# 或激活环境后执行
conda activate {env_name} && python main.py --dev --headless
```

**环境探测**：读取 `environment.yml` 获取 `name` 字段确定环境名

**通过条件**：退出码 0，无严重错误

## 阶段 5：User 无头验证

**执行命令**：

```bash
python main.py --user --headless
```

**检查诊断报告**：`logs/diagnosis/latest/`

**通过条件**：无严重问题

## 阶段 6-7：PR 管理

阶段 5 通过后，直接进入 PR 流程：

1. 提交 Commit
2. 推送到远程
3. 创建 PR
4. 调用 `pr-review` Skill 执行审查流程

## 错误处理

```
测试失败
    │
    ▼
Agent 自诊断（读取 traceback、日志、诊断报告）
    │
    ├─ 可修复 → 修复代码 → 重跑测试
    │
    └─ 不可修复 → 生成分析报告 → 向用户求助
```

## 有头验收（开发者可选）

非标准流程，开发者手动执行观察 UI 行为：

```bash
python main.py --dev  # 可视化模式
```
