# 多智能体框架状态机重构 Spec

## Why

旧框架存在**规则模糊导致的"无限曲解与行为放大"**问题：
- 全局 Rule 包含过多执行细节，导致不同 Agent 看到不该看到的规则
- Agent 之间通过冗长对话传递信息，上下文污染严重
- 缺乏明确的"挂起"机制，Agent 会无限重试

本次重构采用**"状态机（State Machine）+ API 契约"**的工程化设计思路，彻底根治系统复杂度和幻觉放大。

## What Changes

### **BREAKING** 架构重构

1. **全局 Rule 极薄化**：只定义状态路由表与通信协议，移除所有执行细节
2. **基于文件的状态握手**：Agent 之间通过读写特定 Markdown 文件完成交接
3. **Skill 作为动态链接库**：按需加载，不污染全局上下文

### 新增通信媒介文件

| 文件 | 用途 | 写入者 | 读取者 |
|------|------|--------|--------|
| `.trae/current_task.md` | 任务上下文 | Master Agent | 所有子 Agent |
| `.trae/test_report.md` | 测试结果 | test-agent | Master Agent |
| `.trae/blocked_reason.md` | 阻塞原因 | 任意 Agent | Master Agent |

### 新增状态标签字典

| 标签 | 含义 | 触发者 |
|------|------|--------|
| `[REQ_DEV]` | 需要修改业务代码 | Master/test-agent |
| `[REQ_TEST]` | 需要执行测试验证 | Master/dev-agent |
| `[REQ_DOCS]` | 需要同步文档 | Master/test-agent |
| `[BLOCK_NEED_MASTER]` | 子任务受阻，需移交决策 | 任意子 Agent |

## Impact

- 受影响的文件：
  - `.trae/rules/project_rules.md`（全局 Rule 重构）
  - `.trae/prompts/master.md`（Master Agent 配置）
  - `.trae/agents/dev-agent.md`（dev-agent 配置）
  - `.trae/agents/test-agent.md`（test-agent 配置）
  - `.trae/agents/docs-agent.md`（docs-agent 配置）
  - `.trae/skills/*/SKILL.md`（所有 Skill 文件）

## 新增需求

### 需求：三层控制流架构

系统应采用三层控制流设计：

#### 第一层：全局 Rule（路由器与总线）

- 只定义状态路由表与通信协议
- 不包含任何执行步骤
- 所有 Agent 可见

#### 第二层：子 Agent 配置（API 接口）

- 定义不可逾越的边界
- 定义标准输入输出格式
- 定义状态标签输出规则

#### 第三层：Skill 文件（执行引擎）

- 容纳极度细节的操作步骤
- 按需加载，不污染全局上下文

### 需求：强制反推演机制

test-agent 必须遵守以下约束：

- **当** 发现代码有 Bug
- **则** 唯一合法动作是记录报错堆栈并退出
- **禁止** 生成修复代码片段
- **禁止** 提出修复建议
- **必须** 将决策权上交给 Master Agent

### 需求：标准化阻断协议

所有子 Agent 必须遵守以下挂起机制：

- **当** 调用 MCP（如 Playwright 抓取元素）连续 2 次失败
- **则** 必须立即触发 `[BLOCK_NEED_MASTER]` 标签
- **禁止** 继续重试
- **必须** 等待 Master Agent 介入

### 需求：基于文件的记忆锁

复杂指令（超过 5 步）必须通过文件传递：

- Master Agent 将任务细节写入 `.trae/current_task.md`
- 子 Agent 唤醒后的第一步是读取该文件
- 确保每次 Agent 启动时上下文干净、纯粹

### 需求：状态标签输出规范

子 Agent 完成任务后，必须输出状态标签：

#### 场景：test-agent 测试通过

- **当** test-agent 完成测试且全部通过
- **则** 输出 `[REQ_DOCS]` 呼叫文档更新

#### 场景：test-agent 测试失败

- **当** test-agent 完成测试且有失败
- **则** 输出 `[REQ_DEV]` 并附带 `test_report.md` 路径

#### 场景：任意 Agent 遇到阻塞

- **当** 子 Agent 无法继续执行
- **则** 输出 `[BLOCK_NEED_MASTER]` 并说明原因

## 修改的需求

### 需求：全局 Rule 结构

project_rules.md 必须重构为：

```markdown
# 全局多智能体协作协议

## 1. 状态标签字典
[标签定义表]

## 2. 通信媒介
[文件定义表]

## 3. Master Agent 独占守则
[路由规则]
```

### 需求：子 Agent 配置结构

每个子 Agent 配置必须包含：

```markdown
# Identity
[身份定义]

# Constraints（严禁事项）
[边界定义]

# Execution & Routing
[执行流程 + 状态标签输出规则]
```

### 需求：Skill 文件结构

每个 Skill 文件必须：

- 只包含操作步骤，不包含身份定义
- 明确触发条件
- 明确输出格式

## 移除的需求

### 需求：从全局 Rule 移除执行细节

**原因**：执行细节会导致不同 Agent 看到不该看到的规则，产生行为错乱

**迁移**：所有执行细节移入对应的 Skill 文件

### 需求：从子 Agent 配置移除详细流程

**原因**：详细流程会污染 Agent 上下文

**迁移**：详细流程移入 Skill 文件，Agent 按需检索
