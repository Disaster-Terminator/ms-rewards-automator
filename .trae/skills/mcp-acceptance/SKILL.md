---
name: mcp-acceptance
description: 执行 MCP 驱动的 7 阶段验收流程。当代码修改完成需要验收时触发，或用户请求运行验收。
---

# MCP 验收流程

## 执行者分工

| 阶段 | 执行者 | 说明 |
|------|--------|------|
| 1-5 | **test-agent** | 所有测试验收任务统一执行 |
| 6-7 | Master Agent | PR 管理、审查处理、合并决策 |

**Master Agent 职责**：

- 触发 mcp-acceptance skill
- 接收 test-agent 结果摘要
- 失败时路由给 dev-agent 修复
- 成功时通知人工合并

**test-agent 职责**：

- 执行 CI 自动化（阶段 1-3）
- 执行无头验收（阶段 4-5）
- 返回简洁结果摘要（不是完整输出）

**重要**：Master Agent 不应直接执行测试命令，避免测试输出占用上下文。

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

## 阶段 4：Dev 无头验证（不可跳过）

**执行者**：调用 test-agent

**降级执行策略**：

```bash
# 步骤 1：尝试 rscore
rscore --dev --headless

# 步骤 2：如果 rscore 失败，降级到 python main.py
python main.py --dev --headless
```

**禁止跳过**：必须执行降级测试，不能因为 rscore 失败就跳过。

**页面观察**：test-agent 使用 Playwright MCP 观察浏览器页面状态，验证程序运行情况。

**环境探测**：读取 `environment.yml` 或 `pyproject.toml` 确定虚拟环境

**通过条件**：退出码 0，无严重错误

## 阶段 5：User 无头验证（不可跳过）

**执行者**：调用 test-agent

**降级执行策略**：

```bash
# 步骤 1：尝试 rscore
rscore --user --headless

# 步骤 2：如果 rscore 失败，降级到 python main.py
python main.py --user --headless
```

**禁止跳过**：必须执行降级测试，不能因为 rscore 失败就跳过。

**页面观察**：test-agent 使用 Playwright MCP 观察浏览器页面状态，验证程序运行情况。

**检查诊断报告**：`logs/diagnosis/latest/`

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
