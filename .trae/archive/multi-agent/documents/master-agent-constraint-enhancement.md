# Master Agent 约束强化计划（正向指令版）

## 问题诊断

### 违规行为回顾

| 规定                     | 我的违规行为              | 根因            |
| ---------------------- | ------------------- | ------------- |
| 阶段 1-5 由 test-agent 执行 | 我直接执行了 `ruff check` | 提示词没有明确"谁做什么" |
| 测试失败 → 路由给 dev-agent   | 我直接修复了 lint 错误      | 没有明确的正向流程     |

### 根因分析

提示词用了太多"禁止"，没有明确告诉 Agent **要做什么**。

## 改进方案（正向指令）

### 1. 更新 master.md 提示词

**用正向指令替代负面禁令**：

```markdown
## Protocol

### 任务分工
- 代码修改 → dev-agent
- 测试验收 → test-agent
- 文档更新 → docs-agent

### 验收流程
1. 触发 `mcp-acceptance` skill
2. 将测试任务写入 `.trae/current_task.md`
3. 唤醒 test-agent 执行阶段 1-5
4. 收到结果后：
   - 成功 → 进入 PR 流程
   - 失败 → 输出 `[REQ_DEV]`，路由给 dev-agent

### 状态流转
| 收到标签 | 动作 |
|----------|------|
| `[REQ_TEST]` | 唤醒 test-agent |
| `[REQ_DEV]` | 唤醒 dev-agent |
| `[REQ_DOCS]` | 唤醒 docs-agent |
| `[BLOCK_NEED_MASTER]` | 调用 master-recovery skill |
```

### 2. 更新 mcp-acceptance skill

**用正向指令替代前置检查**：

```markdown
## 执行流程

1. Master Agent 将测试任务写入 `.trae/current_task.md`
2. Master Agent 唤醒 test-agent
3. test-agent 执行阶段 1-5
4. test-agent 返回结果摘要
5. Master Agent 根据结果决定下一步：
   - 成功 → 进入阶段 6-7
   - 失败 → 输出 `[REQ_DEV]`
```

### 3. 更新 test-agent.md 提示词

**明确职责**：

```markdown
## Protocol

### 执行序列
1. 读取 `.trae/current_task.md`
2. 阅读 `.trae/skills/test-execution/SKILL.md`
3. 执行测试：
   - 阶段 1：静态检查（ruff）
   - 阶段 2：单元测试（pytest unit）
   - 阶段 3：集成测试（pytest integration）
   - 阶段 4：Dev 无头验证
   - 阶段 5：User 无头验证
4. 输出状态标签

### 状态流转
| 结果 | 标签 |
|------|------|
| 全部通过 | `[REQ_DOCS]` |
| 任一失败 | `[REQ_DEV]` |
```

## 变更清单

| 文件                                     | 变更内容                          |
| -------------------------------------- | ----------------------------- |
| `.trae/prompts/master.md`              | 用"任务分工"替代"禁止"，用"验收流程"替代"禁止测试" |
| `.trae/skills/mcp-acceptance/SKILL.md` | 用执行流程替代前置检查                   |
| `.trae/agents/test-agent.md`           | 明确 5 阶段执行序列                   |

## 对比

| 原版（负面禁令）                   | 改进版（正向指令）                                     |
| -------------------------- | --------------------------------------------- |
| 禁止直接执行 CI 测试命令             | 测试验收 → test-agent                             |
| 禁止测试失败后直接修复                | 失败 → 输出 `[REQ_DEV]`                           |
| 禁止忽略 `[BLOCK_NEED_MASTER]` | 收到 `[BLOCK_NEED_MASTER]` → 调用 master-recovery |

## 预期效果

* Agent 知道"要做什么"，而不是"不能做什么"

* 流程清晰，职责明确

* 减少认知负荷

