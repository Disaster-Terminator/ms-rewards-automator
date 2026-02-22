# 全局多智能体协作协议

当前项目实行状态机驱动开发。所有 Agent 必须遵循以下路由指令与状态标签。

## 1. 状态标签字典（Tags）

Solo Coder 根据以下标签调用对应的子 Agent：

| 标签 | 含义 | 触发者 | 响应动作 |
|------|------|--------|----------|
| `[REQ_DEV]` | 需要修改业务代码 | Master/test-agent | 唤醒 dev-agent |
| `[REQ_TEST]` | 需要执行测试验证 | Master/dev-agent | 唤醒 test-agent |
| `[REQ_DOCS]` | 需要同步文档 | Master/test-agent | 唤醒 docs-agent |
| `[BLOCK_NEED_MASTER]` | 子任务受阻，需移交决策 | 任意子 Agent | 移交 Master Agent |

## 2. 通信媒介（Artifacts）

Agent 之间禁止通过对话直接描述长篇代码逻辑。

| 文件 | 用途 | 写入者 | 读取者 |
|------|------|--------|--------|
| `.trae/current_task.md` | 任务上下文 | Master Agent | 所有子 Agent |
| `.trae/test_report.md` | 测试结果 | test-agent | Master Agent |
| `.trae/blocked_reason.md` | 阻塞原因 | 任意 Agent | Master Agent |

## 3. Master Agent 独占守则

作为 Master，当你看到控制台或上下文出现以下标签时：

| 标签 | 禁止行为 | 必须行为 |
|------|----------|----------|
| `[REQ_TEST]` | 禁止自行测试 | 原样输出标签唤醒 test-agent，发送 `.trae/current_task.md` 路径 |
| `[REQ_DEV]` | 禁止直接修复 | 原样输出标签唤醒 dev-agent，附带上下文 |
| `[BLOCK_NEED_MASTER]` | 禁止忽略 | 读取 `.trae/blocked_reason.md`，做出决策 |

## 4. 身份判定

- 未指定身份 → solo coder（Master Agent），阅读 `.trae/prompts/master.md`
- 指定身份 → 按身份执行

## 5. AI 审查处理

- **必须修复**：`bug_risk`, `Bug`, `security`
- **自主决断**：`suggestion`, `performance`
