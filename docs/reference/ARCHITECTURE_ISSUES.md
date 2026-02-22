# 多智能体框架架构问题与解决方案

## 问题汇总

### 一、架构问题

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 1 | project_rules.md 对所有 agent 可见 | 子 agent 可能执行超出权限的操作（如写入 memory），导致记忆数据混乱 | 高 |
| 2 | Trae 上下文压缩导致仓库信息错乱 | owner/repo 名在压缩后变化（如 `Disaster-Terminator/RewardsCore` 变成 `Disassembler0/RewardsCore-Diagnosis`） | 高 |
| 3 | GitHub MCP 无法正常获取 Qodo 评论 | 只能获取部分评论（如只看到 1 条 security 问题，实际有 7 条） | 中 |

### 二、工作流问题

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 4 | Master Agent 没有 Playwright MCP | 无法执行 E2E 测试，但之前没有意识到这一点 | 已解决 |
| 5 | 子 Agent 调用时机不明确 | 导致 Master Agent 直接执行测试而不是路由给 test-agent | 已解决 |
| 6 | 参数传递问题 | docs-agent 的 owner 参数不正确 | 已解决 |

### 三、审查机器人问题

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 7 | Qodo 评论格式特殊 | 评论包含 HTML 标签和 `<details>` 折叠块，MCP 工具返回的数据被截断 | 中 |
| 8 | 三种审查机器人格式不同 | Sourcery 有 `Prompt for AI Agents`，Copilot 是纯 Markdown，Qodo 有 `Agent Prompt` | 低 |

---

## 解决方案

### 方案 1：身份判定 + 文件结构重组（已讨论确定）

**问题**：

1. project_rules.md 对所有 agent 可见
2. Solo coder（Trae 内置）没有专属提示词，只能通过规则获取身份认知
3. 规则太长浪费上下文

**解决方案**：

#### 文件结构

```
.trae/
├── rules/
│   └── project_rules.md      # 极简：公共规则 + 身份判定 + 路由表
├── agents/                    # 完整配置备份（用户在 UI 创建 agent 时参考）
│   ├── master-agent.md       # 基本信息 + MCP 配置 + 内置工具配置
│   ├── dev-agent.md
│   ├── test-agent.md
│   └── docs-agent.md
├── prompts/                   # 纯提示词（身份认知 + 职责）
│   ├── master.md             # Solo Coder 身份 + 仓库信息 + 调用策略
│   ├── dev.md
│   ├── test.md
│   └── docs.md
└── skills/
    ├── mcp-acceptance/
    ├── pr-review/
    ├── fetch-reviews/        # 待创建：获取审查意见
    └── dispatch-agent/       # 待创建：子 agent 调用标准流程
```

#### project_rules.md（极简版）

```markdown
# RewardsCore 项目规则

## 身份判定
- **如果没有被明确指定身份** → 你是 Trae 内置的 solo coder（Master Agent）
- **如果被明确指定身份** → 按照你的身份阅读对应提示词

## 路由表
| 身份 | 提示词文件 |
|------|-----------|
| solo coder (Master) | `.trae/prompts/master.md` |
| dev-agent | `.trae/prompts/dev.md` |
| test-agent | `.trae/prompts/test.md` |
| docs-agent | `.trae/prompts/docs.md` |

## 公共规则
- Git 规范（Conventional Commits，中文描述）
- 测试规范（改动前后必须运行测试）
- ...
```

#### 子 agent 内置提示词（UI 配置示例）

```
# dev-agent
你是开发智能体（dev-agent）。
详细指令请阅读 `.trae/prompts/dev.md`
```

#### 效果

| Agent | 身份来源 | 行为 |
|-------|---------|------|
| solo coder | 无内置提示词 → 默认 solo coder | 读 master.md |
| dev-agent | 内置提示词明确指定 | 读 dev.md |
| test-agent | 内置提示词明确指定 | 读 test.md |
| docs-agent | 内置提示词明确指定 | 读 docs.md |

---

### 方案 2：仓库信息持久化

**问题**：Trae 上下文压缩导致仓库信息错乱。

**解决方案**：在 `prompts/master.md` 开头写死仓库信息

```markdown
# Solo Coder 提示词

## 仓库信息（不可变）
- owner: `Disaster-Terminator`
- repo: `RewardsCore`
- default_branch: `main`

## 职责
...
```

**备选**：Memory MCP 持久化 + 启动时读取

---

### 方案 3：Qodo 评论完整获取

**问题**：GitHub MCP 的 `get_pull_request_comments` 返回数据被截断。

**解决方案**：使用 WebFetch 直接调用 GitHub API

```
GET https://api.github.com/repos/{owner}/{repo}/pulls/{number}/comments
```

**解析策略**：

1. 过滤 `user.login == "qodo-code-review[bot]"`
2. 解析 `body` 中的 HTML：
   - 提取 `<details><summary><strong>Agent Prompt</strong></summary>` 中的内容
   - 提取 `Fix Focus Areas` 列表

---

### 方案 4：Skill 封装降低上下文压力

**问题**：提示词太长浪费上下文

**解决方案**：将复杂流程封装为 Skill，按需展开

| Skill | 封装内容 | 调用时机 |
|-------|---------|---------|
| `mcp-acceptance` | 7 阶段验收流程 | 代码修改完成后 |
| `pr-review` | PR 审查流程 | PR 创建后 |
| `fetch-reviews` | 获取所有审查机器人评论（Qodo 用 WebFetch，其他用 MCP） | 需要查看审查意见时 |
| `dispatch-agent` | 子 agent 调用标准流程（参数传递、结果解析） | 需要路由任务时 |

**提示词精简效果**：

```markdown
## 审查意见获取
调用 `fetch-reviews` skill

## 子 agent 调用
调用 `dispatch-agent` skill
```

---

### 方案 5：审查机器人统一解析

**Sourcery 解析**：

```
1. 过滤 user.login == "sourcery-ai[bot]"
2. 提取 <details><summary>Prompt for AI Agents</summary> 中的 ~~~markdown 块
3. 解析 Individual Comments 部分
```

**Copilot 解析**：

```
1. 过滤 user.login == "copilot-pull-request-reviewer[bot]"
2. 直接读取 body（纯 Markdown）
```

**Qodo 解析**：

```
1. 过滤 user.login == "qodo-code-review[bot]"
2. 使用 WebFetch 获取完整评论
3. 解析 HTML 提取 Agent Prompt
```

---

## 实施计划

| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 重命名 `.trae/prompts/` 为 `.trae/agents/` | ✅ 已完成 |
| 2 | 新建 `.trae/prompts/` 目录，创建 master.md | ✅ 已完成 |
| 3 | 精简 `project_rules.md`，添加身份判定 | ✅ 已完成 |
| 4 | 创建 `fetch-reviews` skill | ✅ 已完成 |
| 5 | 创建 `dispatch-agent` skill | ❌ 取消（简化流程） |
| 6 | 在 Memory MCP 中持久化仓库信息 | ✅ 已完成 |
| 7 | 完善 MCP 工具配置列表 | ✅ 已完成 |
| 8 | 精简规则文件，移除重复内容 | ✅ 已完成 |

---

## 经验教训

1. **不要假设 MCP 工具返回完整数据**：需要验证返回结果是否完整
2. **上下文压缩会丢失关键信息**：需要持久化锚点
3. **规则文件需要权限隔离**：避免子 agent 越权操作
4. **审查机器人格式各异**：需要统一的解析策略
5. **Skill 封装可降低上下文压力**：按需展开，不调用时不占用上下文
6. **身份判定需要默认值**：Solo coder 无内置提示词，需要通过"未指定身份则默认"机制获取身份

---

## Skill 机制（已验证）

| 问题 | 答案 |
|------|------|
| 触发方式 | 通过 `Skill` 工具主动调用，传入 skill name（如 `mcp-acceptance`） |
| 参数传递 | Skill 本身不接收参数，它是"指令文档"，指导 agent 如何执行 |
| 内部调用工具 | Skill 内容告诉 agent 使用哪些工具（RunCommand、GitHub MCP、WebFetch 等） |

**本质**：Skill 是**按需加载的指令文档**，不调用时不占用上下文，调用后展开详细指令。

**示例调用**：

```
Skill(name="mcp-acceptance")
```

**设计建议**：

- Skill 内可以写"使用 WebFetch 调用 GitHub API"
- Skill 内可以写"使用 Memory MCP 读取仓库信息"
- 参数通过上下文传递（如当前 PR 号、owner/repo 从 Memory 或提示词获取）
